import difflib
import os
import pytest

from test_common import compare_files, get_core, get_synth, vlogdefines, vlogparams

tests_dir = os.path.dirname(__file__)
params = vlogparams + vlogdefines
core = get_core("mor1kx-arty")
backend = get_synth('vivado', core)
ref_dir_base = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_vivado_configure():

    backend.configure(params)

    tcl_file = core.name.sanitized_name + '.tcl'

    ref_dir = os.path.join(ref_dir_base, 'configure')
    compare_files(ref_dir, work_root, [tcl_file])

def test_vivado_build():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.build()

    ref_dir = os.path.join(ref_dir_base, 'build')
    compare_files(ref_dir, work_root, ['run.cmd'])

def test_vivado_pgm():
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.run([])

    ref_dir = os.path.join(ref_dir_base, 'pgm')
    pgm_tcl_file = core.name.sanitized_name + '_pgm.tcl'
    compare_files(ref_dir, work_root, [pgm_tcl_file, 'run.cmd'])
