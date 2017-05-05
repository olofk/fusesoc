import difflib
import os
import pytest

from fusesoc.config import Config
from fusesoc.core import Core
from fusesoc.coremanager import CoreManager
from fusesoc.main import _import

from test_common import get_core

def test_ise():
    tests_dir = os.path.dirname(__file__)
    params = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'
    params += ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'

    core = get_core("atlys")

    backend =_import('build', core.main.backend)(core, export=False)
    backend.configure(params.split())

    tcl_file = core.name.sanitized_name + '.tcl'
    reference_tcl = os.path.join(tests_dir, __name__, tcl_file)
    generated_tcl = os.path.join(backend.work_root, tcl_file)

    assert os.path.exists(generated_tcl)

    with open(reference_tcl) as f1, open(generated_tcl) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        assert diff == ''
