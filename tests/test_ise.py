import pytest

def test_ise():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_ise_0'
    tool         = 'ise'
    tool_options = {
        'family'  : 'spartan6',
        'device'  : 'xc6slx45',
        'package' : 'csg324',
        'speed'   : '-2'
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       'config.mk',
                                       name+'.tcl',
                                       name+'_run.tcl',
    ])

    #f = os.path.join(work_root, 'pcf_file.pcf')
    #with open(f, 'a'):
    #    os.utime(f, None)

    backend.build()
    compare_files(ref_dir, work_root, ['xtclsh.cmd'])

def test_ise_missing_options():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_ise_0'
    tool         = 'ise'
    tool_options = {
        'family'  : 'spartan6',
        'device'  : 'xc6slx45',
        'package' : 'csg324',
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    with pytest.raises(RuntimeError) as e:
        backend.configure('')
    assert "Missing required option 'speed'" in str(e.value)
