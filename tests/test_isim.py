import pytest

def test_isim():
    import os
    import shutil
    import tempfile
    import yaml
    from fusesoc.edatools import get_edatool
    from edalize_common import compare_files, files, param_gen, tests_dir, vpi

    (parameters, args) = param_gen(['plusarg', 'vlogdefine', 'vlogparam'])

    work_root = tempfile.mkdtemp(prefix='isim_')
    eda_api_file = os.path.join(work_root, 'test_isim_0.eda.yml')
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'name'       : 'test_isim_0',
                           'files'      : files,
                           'parameters' : parameters,
                           'tool_options' : {'isim' : {
                               'fuse_options' : ['some', 'fuse_options'],
                               'isim_options' : ['a', 'few', 'isim_options']}},
                           'toplevel'   : 'top_module',
                           'vpi'        :  vpi}))

    backend = get_edatool('isim')(eda_api_file=eda_api_file)
    backend.configure(args)

    ref_dir = os.path.join(tests_dir, __name__)
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
