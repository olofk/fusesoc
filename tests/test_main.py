import pytest

from fusesoc.main import sim

def test_sim(capsys):
    class Args():
        sim = None
        testbench = None
        keep = False
        backendargs = None
        setup = True
        build_only = False
        def __init__(self, system):
            self.system = system

    args = Args(system="wb_common")
    with pytest.raises(SystemExit):
        sim(args)
    out, err = capsys.readouterr()
    assert out == ""
    #Workaround since this test fails with Travis on Python2.7. No idea why
    import sys
    if sys.version_info[0] > 2:
        assert err == "No simulator was supplied on command line or found in 'wb_common' core description\n"
