import pytest

def test_modelsim():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_modelsim_0'
    tool         = 'modelsim'
    tool_options = {
        'vlog_options' : ['some', 'vlog_options'],
        'vsim_options' : ['a', 'few', 'vsim_options'],
    }

    #FIXME: Add VPI tests
    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options, use_vpi=False)
    backend.configure(args)

    compare_files(ref_dir, work_root, [
        'Makefile',
        'edalize_build_rtl.tcl',
        'edalize_main.tcl',
    ])

    orig_env = os.environ.copy()
    os.environ['MODEL_TECH'] = os.path.join(tests_dir, 'mock_commands')

    backend.build()
    os.makedirs(os.path.join(work_root, 'work'))

    compare_files(ref_dir, work_root, ['vsim.cmd'])

    backend.run(args)

    with open(os.path.join(ref_dir, 'vsim2.cmd')) as fref, open(os.path.join(work_root, 'vsim.cmd')) as fgen:
        assert fref.read() == fgen.read()

    os.environ = orig_env
