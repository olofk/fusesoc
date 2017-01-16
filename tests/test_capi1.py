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

    assert len(core.icestorm.export_files) == 1
    assert core.icestorm.export_files[0].name == 'c3demo.pcf'
    assert core.icestorm.arachne_pnr_options == ['-s', '1', '-d', '8k']
    assert core.icestorm.top_module == 'c3demo'
    assert core.icestorm.warnings == []
    
