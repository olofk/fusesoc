import pytest

def test_xsim():
    import os
    import shutil
    import tempfile
    import yaml
    from fusesoc.edatools import get_edatool
    from edalize_common import compare_files, files, param_gen, tests_dir, vpi

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    (parameters, args) = param_gen(['plusarg', 'vlogdefine', 'vlogparam'])

    work_root = tempfile.mkdtemp(prefix='xsim_')
    eda_api_file = os.path.join(work_root, 'test_xsim_0.eda.yml')
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'name'       : 'test_xsim_0',
                           'files'      : files,
                           'parameters' : parameters,
                           'tool_options' : {'xsim' : {
                               'xelab_options' : ['some', 'xelab_options'],
                               'xsim_options'  : ['a', 'few', 'xsim_options']}},
                           'toplevel'   : 'top_module',
                           'vpi'        :  vpi}))

    backend = get_edatool('xsim')(eda_api_file=eda_api_file)
    backend.configure(args)

    ref_dir = os.path.join(tests_dir, __name__)
    compare_files(ref_dir, work_root, ['config.mk',
                                       'Makefile',
                                       'test_xsim_0.prj',
                                       'run-gui.tcl',
                                       'run.tcl'])

    backend.build()

    xsimkdir = os.path.join(work_root, 'xsim.dir', 'test_xsim_0')
    os.makedirs(xsimkdir)
    with open(os.path.join(xsimkdir, 'xsimk'), 'w') as f:
        f.write("I am a compiled simulation kernel\n")
    backend.run(parameters)

    compare_files(ref_dir, work_root, ['run.cmd'])
