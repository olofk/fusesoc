import difflib
import os
import pytest

from fusesoc.core import Core

def compare_fileset(fileset, name, files):
    assert name == fileset.name
    for i in range(len(files)):
        assert files[i] == fileset.file[i].name

def test_core_info():
    tests_dir = os.path.dirname(__file__)
    cores_root = os.path.join(tests_dir, 'cores')
    for core_name in ['sockit', 'mor1kx-generic']:
        core = Core(os.path.join(cores_root, core_name, core_name+'.core'))
        gen_info = '\n'.join([x for x in core.info().split('\n') if not 'Core root' in x])
        with open(os.path.join(tests_dir, __name__, core_name+".info")) as f:
            assert f.read() == gen_info, core_name

def test_core_parsing():
    from fusesoc.vlnv import Vlnv

    cores_root = os.path.join(os.path.dirname(__file__), 'cores', 'misc')
    core = Core(os.path.join(cores_root, 'nomain.core'))
    assert core.name == Vlnv("::nomain:0")

    import sys
    if sys.version_info[0] > 2:
        with pytest.raises(SyntaxError) as e:
            core = Core(os.path.join(cores_root, "duplicateoptions.core"))
        assert "option 'file_type' in section 'fileset dummy' already exists" in str(e.value)

def test_capi1_get_parameters():
    tests_dir = os.path.join(os.path.dirname(__file__),
                             __name__)

    with pytest.raises(SyntaxError) as e:
        core = Core(os.path.join(tests_dir, 'parameters_nodatatype.core'))
    assert "Invalid datatype '' for parameter" in str(e.value)

    with pytest.raises(SyntaxError) as e:
        core = Core(os.path.join(tests_dir, 'parameters_invaliddatatype.core'))
    assert "Invalid datatype 'badtype' for parameter" in str(e.value)

    with pytest.raises(SyntaxError) as e:
        core = Core(os.path.join(tests_dir, 'parameters_noparamtype.core'))
    assert "Invalid paramtype '' for parameter" in str(e.value)

    with pytest.raises(SyntaxError) as e:
        core = Core(os.path.join(tests_dir, 'parameters_invalidparamtype.core'))
    assert "Invalid paramtype 'badtype' for parameter" in str(e.value)
    
                
def test_get_scripts():
    flag_combos = [{'target' : 'sim'  , 'is_toplevel' : False},
                   {'target' : 'sim'  , 'is_toplevel' : True},
                   {'target' : 'synth', 'is_toplevel' : False},
                   {'target' : 'synth', 'is_toplevel' : True},
    ]
    filename = os.path.join(os.path.dirname(__file__), 'cores', 'misc', 'scriptscore.core')
    core = Core(filename, '', 'dummy_build_root')

    for flags in flag_combos:
        env = {
            'BUILD_ROOT' : 'dummy_build_root',
            'FILES_ROOT' : 'dummyroot'
        }
        result = core.get_scripts("dummyroot", flags)
        expected = {}
        if flags['target'] == 'sim':
            sections = ['post_run', 'pre_build', 'pre_run']
        else:
            if flags['is_toplevel']:
                env['SYSTEM_ROOT'] = core.files_root
                sections = ['pre_build', 'post_build']
            else:
                sections = []
        for section in sections:
            _name = flags['target']+section+'_scripts{}'
            expected[section] = [{'cmd' : ['sh', os.path.join('dummyroot', _name.format(i))],
                                  'name' : _name.format(i),
                                  'env' : env} for i in range(2)]
        assert expected == result

def test_get_tool():
    cores_root = os.path.join(os.path.dirname(__file__), 'cores')

    core = Core(os.path.join(cores_root, 'atlys', 'atlys.core'))
    assert None     == core.get_tool({'target' : 'sim', 'tool' : None})
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : 'icarus'})
    assert 'ise'    == core.get_tool({'target' : 'synth', 'tool' : None})
    assert 'vivado' == core.get_tool({'target' : 'synth', 'tool' : 'vivado'})

    core = Core(os.path.join(cores_root, 'sockit', 'sockit.core'))
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : None})
    assert 'icarus' == core.get_tool({'target' : 'sim', 'tool' : 'icarus'})
    del core.main.backend
    assert None     == core.get_tool({'target' : 'synth', 'tool' : None})
    assert 'vivado' == core.get_tool({'target' : 'synth', 'tool' : 'vivado'})
    core.main.backend = 'quartus'

def test_get_tool_options():
    cores_root = os.path.join(os.path.dirname(__file__), 'cores')

    core = Core(os.path.join(cores_root, 'mor1kx-generic', 'mor1kx-generic.core'))
    assert {'iverilog_options' : ['-DSIM']} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'icarus'})
    assert {} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'modelsim'})
    assert {'fuse_options' : ['some','isim','options']} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'isim'})
    expected = {'xelab_options' : ['--timescale 1ps/1ps', '--debug typical',
                                   'dummy', 'options', 'for', 'xelab']}
    assert expected == core.get_tool_options({'is_toplevel' : True, 'tool' : 'xsim'})
    assert {} == core.get_tool_options({'is_toplevel' : False, 'tool' : 'icarus'})

    core = Core(os.path.join(cores_root, 'elf-loader', 'elf-loader.core'))
    assert {'libs' : ['-lelf']} == core.get_tool_options({'is_toplevel' : False, 'tool' : 'verilator'})
    assert {} == core.get_tool_options({'is_toplevel' : True, 'tool' : 'invalid'})

def test_get_toplevel():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "atlys.core")
    core = Core(filename)
    assert 'orpsoc_tb'  == core.get_toplevel({'tool' : 'icarus'})
    assert 'orpsoc_tb'  == core.get_toplevel({'tool' : 'icarus', 'testbench' : None})
    assert 'tb'         == core.get_toplevel({'tool' : 'icarus', 'testbench' : 'tb'})
    assert 'orpsoc_top' == core.get_toplevel({'tool' : 'vivado'})
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "sockit.core")
    core = Core(filename)
    assert 'dummy_tb'   == core.get_toplevel({'tool' : 'icarus'})
    assert 'dummy_tb'   == core.get_toplevel({'tool' : 'icarus', 'testbench' : None})
    assert 'tb'         == core.get_toplevel({'tool' : 'icarus', 'testbench' : 'tb'})
    assert 'orpsoc_top' == core.get_toplevel({'tool' : 'vivado'})

def test_icestorm():
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "c3demo.core")
    core = Core(filename)
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
    core = Core(filename)

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
    core = Core(filename)

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
    core = Core(filename)
    assert core.simulator['toplevel'] == 'testbench'

    #Implicit toplevel
    filename = os.path.join(os.path.dirname(__file__),
                            __name__,
                            "atlys.core")
    core = Core(filename)
    assert core.simulator['toplevel'] == 'orpsoc_tb'

def test_verilator():
    cores_root = os.path.join(os.path.dirname(__file__), __name__)

    core = Core(os.path.join(cores_root, "verilator_managed_systemc.core"))
    expected = {'cli_parser' : 'managed', 'libs' : [], 'mode' : 'sc'}
    assert expected == core.get_tool_options({'is_toplevel' : True, 'tool' : 'verilator'})

    assert len(core.file_sets) == 2
    compare_fileset(core.file_sets[0], 'verilator_src_files', ['file1.sc', 'file2.sc'])
    assert core.file_sets[0].file[0].file_type == 'systemCSource'
    assert core.file_sets[0].file[1].file_type == 'systemCSource'

    compare_fileset(core.file_sets[1], 'verilator_tb_toplevel', [])
