import difflib
import os
import shutil
import pytest

from test_common import cmdlineargs, compare_file, get_core, get_sim, vlogdefines, vlogparams

params    = vlogparams + vlogdefines + cmdlineargs
tests_dir = os.path.dirname(__file__)
core      = get_core("mor1kx-generic")
backend   = get_sim('verilator', core)
ref_dir   = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_verilator_configure():
    backend.configure(params)

    assert '' == compare_file(ref_dir, work_root, 'config.mk')
    assert '' == compare_file(ref_dir, work_root, 'Makefile')
    assert '' == compare_file(ref_dir, work_root, core.sanitized_name+'.vc')

def test_verilator_run():
    dummy_exe = 'V'+core.verilator.top_module
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))

    backend.run(params)

    assert '' == compare_file(ref_dir, work_root, 'run.cmd')
