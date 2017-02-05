import filecmp
import os
import pytest

from fusesoc.core import Core
from fusesoc.coremanager import CoreManager
from fusesoc.main import _get_core, _import

def test_ise():
    params = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'
    params += ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'
    cores_root = os.path.join(os.path.dirname(__file__),
                              'cores')
    CoreManager().add_cores_root(cores_root)
    core = _get_core("atlys")

    backend =_import('build', core.main.backend)(core, export=False)
    backend.configure(params.split())

    tcl_file = core.name.sanitized_name + '.tcl'
    reference_tcl = os.path.join(os.path.dirname(__file__), __name__, tcl_file)
    generated_tcl = os.path.join(backend.work_root, tcl_file)

    assert os.path.exists(generated_tcl)
    assert filecmp.cmp(generated_tcl, reference_tcl)
