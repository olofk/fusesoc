import pytest

def test_vivado():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_vivado_0'
    tool         = 'vivado'
    tool_options = {
        'part' : 'xc7a35tcsg324-1',
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, [
        'Makefile',
        name+'.tcl',
        name+'_run.tcl',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'vivado.cmd',
    ])

def test_vivado_minimal():
    import os
    import shutil
    import tempfile

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'vivado'
    name = 'test_vivado_minimal_0'
    work_root = tempfile.mkdtemp(prefix=tool+'_')

    eda_api = {'name'         : name}

    backend = get_edatool(tool)(eda_api=eda_api, work_root=work_root)
    backend.configure([])

    compare_files(ref_dir, work_root, [
        'Makefile',
        name+'.tcl',
        name+'_run.tcl',
    ])

    backend.build()
    compare_files(ref_dir, work_root, [
        'vivado.cmd',
    ])
