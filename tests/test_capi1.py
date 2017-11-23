import difflib
import os
import pytest

from fusesoc.core import Core

from test_common import get_core, cache_root, build_root
def compare_fileset(fileset, name, files):
    assert name == fileset.name
    for i in range(len(files)):
        assert files[i] == fileset.file[i].name

def compare_file(ref_dir, work_root, name):
    import difflib
    import os
    reference_file = os.path.join(ref_dir, name)
    generated_file = os.path.join(work_root, name)

    assert os.path.exists(generated_file)

    with open(reference_file) as f1, open(generated_file) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        return diff

def test_core_info():
    tests_dir = os.path.dirname(__file__)

    core = get_core("sockit")
    gen_info = [x+'\n' for x in core.info().split('\n') if not 'Core root' in x]

    with open(os.path.join(tests_dir, __name__, "sockit.info")) as f:
        ref_info = [x for x in f.readlines() if not 'Core root' in x]
    assert '' == ''.join(difflib.unified_diff(ref_info, gen_info))

def test_core_parsing():
    from fusesoc.vlnv import Vlnv
    core = get_core("nomain")
    assert core.name == Vlnv("::nomain:0")

    from fusesoc.core import Core
    import sys
    if sys.version_info[0] > 2:
        with pytest.raises(SyntaxError) as e:
            core = Core("tests/cores/misc/duplicateoptions.core", cache_root, build_root)
        assert "option 'file_type' in section 'fileset dummy' already exists" in str(e.value)

def test_get_scripts():
    import pprint
    flag_combos = [{'target' : 'sim'  , 'is_toplevel' : False},
                   {'target' : 'sim'  , 'is_toplevel' : True},
                   {'target' : 'synth', 'is_toplevel' : False},
                   {'target' : 'synth', 'is_toplevel' : True},
    ]
    core = get_core("scriptscore")

    for flags in flag_combos:
        env = {'BUILD_ROOT' : os.path.join(os.path.dirname(__file__), 'build')}
        result = core.get_scripts(flags)
        expected = {}
        if flags['target'] == 'sim':
            sections = ['post_run_scripts', 'pre_build_scripts', 'pre_run_scripts']
        else:
            if flags['is_toplevel']:
                env['SYSTEM_ROOT'] = core.files_root
                sections = ['pre_build_scripts', 'post_build_scripts']
            else:
                sections = []
        for section in sections:
            expected[section] = [{flags['target'] + section + str(i) : {'env' : env}} for i in range(2)]
        assert pprint.pformat(expected) == pprint.pformat(result)

def test_get_tool():
    core = get_core("atlys")
    assert None     == core.get_tool({'target' : 'sim', 'tool' : None})
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : 'icarus'})
    assert 'ise'    == core.get_tool({'target' : 'synth', 'tool' : None})
    assert 'vivado' == core.get_tool({'target' : 'synth', 'tool' : 'vivado'})
    core = get_core("sockit")
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : None})
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : 'icarus'})
    del core.main.backend
    assert None     == core.get_tool({'target' : 'synth', 'tool' : None})
    assert 'vivado' == core.get_tool({'target' : 'synth', 'tool' : 'vivado'})
    core.main.backend = 'quartus'

def test_get_tool_options():
    core = get_core("mor1kx-generic")
    assert {'iverilog_options' : ['-DSIM']} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'icarus'})
    assert {} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'modelsim'})
    assert {} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'isim'})
    assert {} == core.get_tool_options({'is_toplevel' : False, 'tool' : 'icarus'})
    core = get_core("elf-loader")
    assert {'libs' : ['-lelf']} == core.get_tool_options({'is_toplevel' : False, 'tool' : 'verilator'})
def test_get_toplevel():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "atlys.core")
    core = Core(filename, cache_root, build_root)
    assert 'orpsoc_tb'  == core.get_toplevel({'tool' : 'icarus'})
    assert 'orpsoc_tb'  == core.get_toplevel({'tool' : 'icarus', 'testbench' : None})
    assert 'tb'         == core.get_toplevel({'tool' : 'icarus', 'testbench' : 'tb'})
    assert 'orpsoc_top' == core.get_toplevel({'tool' : 'vivado'})
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "sockit.core")
    core = Core(filename, cache_root, build_root)
    assert 'dummy_tb'   == core.get_toplevel({'tool' : 'icarus'})
    assert 'dummy_tb'   == core.get_toplevel({'tool' : 'icarus', 'testbench' : None})
    assert 'tb'         == core.get_toplevel({'tool' : 'icarus', 'testbench' : 'tb'})
    assert 'orpsoc_top' == core.get_toplevel({'tool' : 'vivado'})

def test_icestorm():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "c3demo.core")
    core = Core(filename, cache_root, build_root)
    assert len(core.file_sets) == 3
    compare_fileset(core.file_sets[0], 'rtl_files', ['c3demo.v', 'ledpanel.v','picorv32.v'])
    compare_fileset(core.file_sets[1], 'tb_files' , ['firmware.hex', '$YOSYS_DAT_DIR/ice40/cells_sim.v', 'testbench.v'])

    #Check that backend files are converted to fileset properly
    compare_fileset(core.file_sets[2], 'backend_files', ['c3demo.pcf'])
    assert core.file_sets[2].file[0].file_type == 'PCF'

    assert core.icestorm.export_files == []
    assert core.icestorm.arachne_pnr_options == ['-s', '1', '-d', '8k']
    assert core.icestorm.top_module == 'c3demo'
    assert core.icestorm.warnings == []
    
def test_ise():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "atlys.core")
    core = Core(filename, cache_root, build_root)

    #Check filesets
    assert len(core.file_sets) == 4
    assert core.file_sets[0].name == 'verilog_src_files'
    assert core.file_sets[1].name == 'verilog_tb_src_files'
    assert core.file_sets[2].name == 'verilog_tb_private_src_files'

    #Check that backend files are converted to fileset properly
    compare_fileset(core.file_sets[3], 'backend_files', ['data/atlys.ucf'])
    assert core.file_sets[3].file[0].file_type == 'UCF'

    #Check backend section
    assert core.ise.export_files == []
    assert core.ise.family == 'spartan6'
    assert core.ise.device == 'xc6slx45'
    assert core.ise.package == 'csg324'
    assert core.ise.speed == '-2'
    assert core.ise.top_module == 'orpsoc_top'

    assert core.ise.warnings == []

def test_quartus():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "sockit.core")
    core = Core(filename, cache_root, build_root)

    #Check filesets
    assert len(core.file_sets) == 4
    assert core.file_sets[0].name == 'verilog_src_files'
    assert core.file_sets[1].name == 'verilog_tb_src_files'
    assert core.file_sets[2].name == 'verilog_tb_private_src_files'

    #Check that backend files are converted to fileset properly
    assert len(core.file_sets[3].file) == 3
    compare_fileset(core.file_sets[3], 'backend_files', ['data/sockit.qsys', 'data/sockit.sdc', 'data/pinmap.tcl'])
    assert core.file_sets[3].file[0].file_type == 'QSYS'
    assert core.file_sets[3].file[1].file_type == 'SDC'
    assert core.file_sets[3].file[2].file_type == 'tclSource'

    #Check backend section
    assert core.quartus.quartus_options == '--64bit'
    assert core.quartus.family == '"Cyclone V"'
    assert core.quartus.device == '5CSXFC6D6F31C8ES'
    assert core.quartus.top_module == 'orpsoc_top'

    assert core.quartus.warnings == []

def test_simulator():
    #Explicit toplevel
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "c3demo.core")
    core = Core(filename, cache_root, build_root)
    assert core.simulator['toplevel'] == 'testbench'

    #Implicit toplevel
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "atlys.core")
    core = Core(filename, cache_root, build_root)
    assert core.simulator['toplevel'] == 'orpsoc_tb'
