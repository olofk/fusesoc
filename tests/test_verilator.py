import difflib
import os
import shutil
import pytest

from fusesoc.config import Config
from fusesoc.core import Core
from fusesoc.coremanager import CoreManager
from fusesoc.main import _get_core, _import

def compare_file(ref_dir, work_root, name):
    reference_file = os.path.join(ref_dir, name)
    generated_file = os.path.join(work_root, name)

    assert os.path.exists(generated_file)

    with open(reference_file) as f1, open(generated_file) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        return diff
    
def test_verilator_configure():
    tests_dir = os.path.dirname(__file__)
    params = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'
    params += ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'
    params += ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'

    Config().build_root = os.path.join(tests_dir, 'build')
    Config().cache_root = os.path.join(tests_dir, 'cache')
    cores_root = os.path.join(tests_dir, 'cores')

    CoreManager().add_cores_root(cores_root)
    core = _get_core("mor1kx-generic")

    sim_name = 'verilator'
    CoreManager().tool = sim_name
    backend =_import('simulator', sim_name)(core, export=False)

    ref_dir   = os.path.join(tests_dir, __name__)
    work_root = backend.work_root

    backend.configure(params.split())

    assert '' == compare_file(ref_dir, work_root, 'config.mk')
    assert '' == compare_file(ref_dir, work_root, 'Makefile')
    assert '' == compare_file(ref_dir, work_root, core.sanitized_name+'.vc')

def test_verilator_run():
    tests_dir = os.path.dirname(__file__)
    params = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'
    params += ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'
    params += ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'

    Config().build_root = os.path.join(tests_dir, 'build')
    Config().cache_root = os.path.join(tests_dir, 'cache')
    cores_root = os.path.join(tests_dir, 'cores')

    CoreManager().add_cores_root(cores_root)
    core = _get_core("mor1kx-generic")

    sim_name = 'verilator'
    CoreManager().tool = sim_name
    backend =_import('simulator', sim_name)(core, export=False)

    ref_dir   = os.path.join(tests_dir, __name__)
    work_root = backend.work_root

    dummy_exe = 'V'+core.verilator.top_module
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))
    backend.run(params.split())

    assert '' == compare_file(ref_dir, work_root, 'run.cmd')
