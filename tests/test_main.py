import pytest

from fusesoc.main import sim

def test_sim(capsys):
    class Args():
        sim = None
        testbench = None
        keep = False
        plusargs = None
        setup = True
        build_only = False
        def __init__(self, system):
            self.system = system

    args = Args(system="wb_common")
    with pytest.raises(SystemExit):
        sim(args)
    out, err = capsys.readouterr()
    assert out == ""
    assert err == "No simulator was supplied on command line or found in 'wb_common' core description\n"
