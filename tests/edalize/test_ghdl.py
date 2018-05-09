import pytest

def test_ghdl():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogparam']
    name         = 'test_ghdl'
    tool         = 'ghdl'
    tool_options = {'analyze_options' : ['some', 'analyze_options'],
                    'run_options'     : ['a', 'few', 'run_options']}

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile'])

    backend.build()
    compare_files(ref_dir, work_root, ['analyze.cmd'])

    backend.run(args)
    compare_files(ref_dir, work_root, ['elab-run.cmd'])
