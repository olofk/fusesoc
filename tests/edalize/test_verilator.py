import difflib
import os
import shutil
import pytest

from edalize_common import compare_files

tool      = 'verilator'
tests_dir = os.path.dirname(__file__)
ref_dir   = os.path.join(tests_dir, __name__)
core_name = 'mor1kx-generic_0'

cmdlineargs = ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'.split()
vlogdefines = ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'.split()
vlogparams  = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'.split()
params    = vlogparams + vlogdefines + cmdlineargs

def test_verilator_configure():
    import os.path
    import tempfile
    import yaml
    from edalize import get_edatool

    for mode in ['cc', 'sc', 'lint-only']:
        work_root    = tempfile.mkdtemp()
        eda_api_file = os.path.join(ref_dir, mode, core_name) + '.eda.yml'

        backend = get_edatool(tool)(eda_api=yaml.load(open(eda_api_file)), work_root=work_root)

        if mode is 'cc':
            _params = params
        else:
            _params = []
        backend.configure(_params)

        compare_files(ref_dir, work_root, ['Makefile'])

        compare_files(os.path.join(ref_dir, mode),
                      work_root,
                      ['config.mk', core_name+'.vc'])

def test_verilator_run():
    import os.path
    import tempfile
    import yaml
    from edalize import get_edatool
    ref_dir_cc = os.path.join(ref_dir, 'cc')

    work_root    = tempfile.mkdtemp()
    eda_api_file = os.path.join(ref_dir_cc, core_name)+ '.eda.yml'
    backend = get_edatool(tool)(eda_api=yaml.load(open(eda_api_file)), work_root=work_root)
    dummy_exe = 'V'+backend.tool_options['top_module']
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))

    backend.run(params)

    compare_files(ref_dir, work_root, ['run.cmd'])
