import pytest

from fusesoc.main import sim
from fusesoc.coremanager import CoreManager
from fusesoc.config import Config

from test_common import cache_root, cores_root, tests_dir

@pytest.mark.xfail
def test_sim(capsys):

    class Args():
        sim = None
        testbench = None
        target = None
        keep = False
        backendargs = None
        setup = True
        build_only = False
        no_export = False
        def __init__(self, system):
            self.system = system

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager

    build_root = os.path.join(tests_dir, 'build')
    config = Config()
    config.build_root = build_root
    config.cache_root = cache_root

    common_cm = CoreManager(config)
    common_cm.add_cores_root(cores_root)
    args = Args(system="wb_common")
    with pytest.raises(SystemExit):
        sim(common_cm, args)
    out, err = capsys.readouterr()
    assert out == ""
    #Workaround since this test fails with Travis on Python2.7. No idea why
    import sys
    if sys.version_info[0] > 2:
        assert err == "No tool was supplied on command line or found in 'wb_common' core description\n"
