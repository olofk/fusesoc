import os
import pytest

from test_common import compare_files, get_core, get_sim, vlogparams

tests_dir = os.path.dirname(__file__)
core      = get_core("ghdltest")
backend   = get_sim('ghdl', core)
ref_dir   = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_ghdl_configure():

    backend.configure(vlogparams)

    compare_files(ref_dir, work_root, ['Makefile'])

def test_ghdl_build():

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']

    backend.build()
    assert os.path.isfile(os.path.join(work_root, 'pre_build_script_executed'))

def test_ghdl_run():

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    backend.run(vlogparams)

    compare_files(ref_dir, work_root, ['run.cmd'])
    assert os.path.isfile(os.path.join(work_root, 'pre_run_script_executed'))
    assert os.path.isfile(os.path.join(work_root, 'post_run_script_executed'))
