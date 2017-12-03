import os
import pytest

from test_common import compare_files, get_core, get_sim, sim_params

tests_dir = os.path.dirname(__file__)
core      = get_core("mor1kx-generic")
backend   = get_sim('xsim', core)
ref_dir   = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_xsim_configure():

    backend.configure(sim_params)

    compare_files(ref_dir, work_root, ['config.mk',
                                       'Makefile',
                                       core.sanitized_name+'.prj',
                                       'run-gui.tcl',
                                       'run.tcl'])

def test_xsim_build():
    import subprocess
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']

    backend.build()
    assert os.path.isfile(os.path.join(work_root, 'pre_build_script_executed'))

def test_xsim_run():

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    xsimkdir = os.path.join(work_root, 'xsim.dir', core.sanitized_name)
    os.makedirs(xsimkdir)
    with open(os.path.join(xsimkdir, 'xsimk'), 'w') as f:
        f.write("I am a compiled simulation kernel\n")
    backend.run(sim_params)

    compare_files(ref_dir, work_root, ['run.cmd'])
    assert os.path.isfile(os.path.join(work_root, 'pre_run_script_executed'))
    assert os.path.isfile(os.path.join(work_root, 'post_run_script_executed'))
