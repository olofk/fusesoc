import pytest

def test_xsim():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['plusarg', 'vlogdefine', 'vlogparam']
    name         = 'test_xsim_0'
    tool         = 'xsim'
    tool_options = {'xelab_options' : ['some', 'xelab_options'],
                    'xsim_options'  : ['a', 'few', 'xsim_options']}

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['config.mk',
                                       'Makefile',
                                       name+'.prj',
                                       'run-gui.tcl',
                                       'run.tcl'])

    backend.build()
    compare_files(ref_dir, work_root, ['xelab.cmd'])

    xsimkdir = os.path.join(work_root, 'xsim.dir', name)
    os.makedirs(xsimkdir)
    with open(os.path.join(xsimkdir, 'xsimk'), 'w') as f:
        f.write("I am a compiled simulation kernel\n")
    backend.run(args)

    compare_files(ref_dir, work_root, ['xsim.cmd'])
