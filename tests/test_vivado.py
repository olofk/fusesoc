import difflib
import os
import pytest

from test_common import compare_file, get_core, get_synth, vlogdefines, vlogparams

tests_dir = os.path.dirname(__file__)
params = vlogparams + vlogdefines
core = get_core("mor1kx-arty")
backend = get_synth('vivado', core)
ref_dir = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_vivado_configure():

    backend.configure(params)

    tcl_file = core.name.sanitized_name + '.tcl'

    assert '' == compare_file(ref_dir, work_root, tcl_file)

def test_vivado_build():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.build()

    assert '' == compare_file(ref_dir, work_root, 'run.cmd')
