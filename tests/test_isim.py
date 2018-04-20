import pytest

def test_isim():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_isim_0'
    tool         = 'isim'
    tool_options = {
        'fuse_options' : ['some', 'fuse_options'],
        'isim_options' : ['a', 'few', 'isim_options'],
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root,
                  ['config.mk',
                   'Makefile',
                   'run_test_isim_0.tcl',
                   'test_isim_0.prj'])

    dummy_exe = 'test_isim_0'
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))

    backend.run([])

    compare_files(ref_dir, work_root, ['run.cmd'])
