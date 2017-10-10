import difflib
import os
import pytest

from fusesoc.config import Config
from fusesoc.core import Core
from fusesoc.coremanager import CoreManager

from test_common import get_core, get_synth, vlogdefines, vlogparams

def test_ise():
    tests_dir = os.path.dirname(__file__)
    params = vlogparams + vlogdefines

    core = get_core("atlys")

    backend = get_synth('ise', core)
    backend.configure(params)

    tcl_file = core.name.sanitized_name + '.tcl'
    reference_tcl = os.path.join(tests_dir, __name__, tcl_file)
    generated_tcl = os.path.join(backend.work_root, tcl_file)

    assert os.path.exists(generated_tcl)

    with open(reference_tcl) as f1, open(generated_tcl) as f2:
        assert f1.read() == f2.read()
