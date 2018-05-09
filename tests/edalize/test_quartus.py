import pytest

def test_quartus():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_quartus_0'
    tool         = 'quartus'
    tool_options = {
        'family'          : 'Cyclone V',
        'device'          : '5CSXFC6D6F31C8ES',
        'quartus_options' : ['some', 'quartus_options'],
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       'config.mk',
                                       name+'.tcl'])

    backend.build()
    compare_files(ref_dir, work_root, [
        'ip-generate.cmd',
        'quartus_asm.cmd',
        'quartus_fit.cmd',
        'quartus_sh.cmd',
        'quartus_sta.cmd',
    ])
