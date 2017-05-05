import difflib
import os
import pytest

from test_common import compare_file, get_core, get_synth, vlogdefines, vlogparams

tests_dir = os.path.dirname(__file__)
params = vlogparams + vlogdefines
core = get_core("c3demo")
backend = get_synth('icestorm', core)
ref_dir = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_icestorm_configure():

    backend.configure(params)

    ys_file = core.name.sanitized_name + '.ys'

    assert '' == compare_file(ref_dir, work_root, "Makefile")
    assert '' == compare_file(ref_dir, work_root, "config.mk")
    assert '' == compare_file(ref_dir, work_root, ys_file)

def test_icestorm_build():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.build(params)

    assert '' == compare_file(ref_dir, work_root, 'run.cmd')
