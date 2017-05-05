import difflib
import os
import pytest

from test_common import compare_file, get_core, get_synth, vlogdefines, vlogparams

def test_quartus():
    tests_dir = os.path.dirname(__file__)
    params = vlogparams + vlogdefines

    core = get_core("sockit")

    backend = get_synth('quartus', core)
    backend.configure(params)

    tcl_file = core.name.sanitized_name + '.tcl'
    ref_dir = os.path.join(tests_dir, __name__)

    assert '' == compare_file(ref_dir, backend.work_root, tcl_file)
