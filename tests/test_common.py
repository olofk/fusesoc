import os

tests_dir = os.path.dirname(__file__)
build_root = os.path.join(tests_dir, 'build')
cache_root = os.path.join(tests_dir, 'cache')
cores_root = os.path.join(tests_dir, 'cores')
library_root = os.path.join(tests_dir, 'libraries')

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager

config = Config()
config.build_root = build_root
config.cache_root = cache_root
common_cm = CoreManager(config)
common_cm.add_cores_root(cores_root)

def compare_files(ref_dir, work_root, files):
    import difflib

    for f in files:
        reference_file = os.path.join(ref_dir, f)
        generated_file = os.path.join(work_root, f)

        assert os.path.exists(generated_file)

        with open(reference_file) as fref, open(generated_file) as fgen:
            assert fref.read() == fgen.read(), f

def get_core(core):
    from fusesoc.main import _get_core
    
    return _get_core(common_cm, core)

cmdlineargs = ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'.split()
vlogdefines = ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'.split()
vlogparams  = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'.split()
