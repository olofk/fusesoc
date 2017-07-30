import difflib
import os
import pytest

from test_common import compare_files, get_core, get_synth, vlogdefines, vlogparams

tests_dir = os.path.dirname(__file__)
core = get_core("sockit")
backend = get_synth('quartus', core)
work_root = backend.work_root

def test_quartus_configure():
    params = vlogparams + vlogdefines

    backend.configure(params)

    ref_dir = os.path.join(tests_dir, __name__)

    files = ['config.mk',
             'Makefile',
             'sockit_1_0.tcl']
    compare_files(ref_dir, work_root, files)

def test_quartus_build():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.build()

def test_quartus_pgm():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.pgm([])
