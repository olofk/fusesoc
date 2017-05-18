import os
import shutil
import pytest

from test_common import compare_file, get_core, get_sim, sim_params

tests_dir = os.path.dirname(__file__)
core      = get_core("mor1kx-generic")
backend   = get_sim('icarus', core)
ref_dir   = os.path.join(tests_dir, __name__)
work_root = backend.work_root


def test_icarus_configure():

    backend.configure(sim_params)

    assert '' == compare_file(ref_dir, work_root, core.sanitized_name+'.scr')

def test_icarus_run():

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']

    backend.run(sim_params)

    assert '' == compare_file(ref_dir, work_root, 'run.cmd')
