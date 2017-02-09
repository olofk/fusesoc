import os
import pytest

from fusesoc.core import Core

def compare_fileset(fileset, name, files):
    assert name == fileset.name
    for i in range(len(files)):
        assert files[i] == fileset.file[i].name

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
