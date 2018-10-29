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
        'timescale'        : '1ns/1ns',
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options, use_vpi=True)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr',
                                       'timescale.v',
    ])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])
    compare_files(ref_dir, work_root, ['iverilog-vpi.cmd'])

    backend.run(args)

    compare_files(ref_dir, work_root, ['vvp.cmd'])

def test_icarus_minimal():
    import os
    import shutil
    import tempfile

    from edalize import get_edatool

    from edalize_common import compare_files, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    tool = 'icarus'
    name = 'test_'+tool+'_minimal_0'
    work_root = tempfile.mkdtemp(prefix=tool+'_')

    eda_api = {'name'         : name,
               'toplevel' : 'top'}

    backend = get_edatool(tool)(eda_api=eda_api, work_root=work_root)
    backend.configure([])

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.scr',
    ])

    backend.build()
    compare_files(ref_dir, work_root, ['iverilog.cmd'])

    backend.run([])

    compare_files(ref_dir, work_root, ['vvp.cmd'])
