import pytest

def test_icarus():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_icarus_0'
    tool         = 'icarus'
    tool_options = {
        'iverilog_options' : ['some', 'iverilog_options'],
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options, use_vpi=True)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr'])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])
    compare_files(ref_dir, work_root, ['iverilog-vpi.cmd'])

    backend.run(args)

    compare_files(ref_dir, work_root, ['vvp.cmd'])
