import difflib
import os
import pytest

from test_common import get_core, get_synth, vlogdefines, vlogparams

tests_dir = os.path.dirname(__file__)
core = get_core("sockit")
backend = get_synth('quartus', core)
work_root = backend.work_root

def test_quartus_configure():
    params = vlogparams + vlogdefines

    backend.configure(params)

    tcl_file = core.name.sanitized_name + '.tcl'
    ref_dir = os.path.join(tests_dir, __name__)

    for f in ['config.mk',
              'Makefile',
              'sockit_0.tcl']:
        with open(os.path.join(ref_dir, f)) as fref, open(os.path.join(work_root, f)) as fgen:
            assert fref.read() == fgen.read(), f

def test_quartus_build():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.build(None)

def test_quartus_pgm():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.pgm([])
