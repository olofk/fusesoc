import difflib
import os
import shutil
import pytest

from test_common import cmdlineargs, compare_files, get_core, vlogdefines, vlogparams

tool      = 'verilator'
params    = vlogparams + vlogdefines + cmdlineargs
tests_dir = os.path.dirname(__file__)
core      = get_core("mor1kx-generic")
ref_dir   = os.path.join(tests_dir, __name__)

def test_verilator_configure():
    import os.path
    import tempfile
    from fusesoc.utils import _import

    for mode in ['cc', 'sc', 'lint-only']:
        work_root    = tempfile.mkdtemp()
        eda_api_file = os.path.join(ref_dir, mode, core.name.sanitized_name) + '.eda.yml'

        backend = _import(tool, 'edatools')(eda_api_file=eda_api_file, work_root=work_root)

        if mode is 'cc':
            _params = params
        else:
            _params = []
        backend.configure(_params)

        compare_files(ref_dir, work_root, ['Makefile'])

        compare_files(os.path.join(ref_dir, mode),
                      work_root,
                      ['config.mk', core.sanitized_name+'.vc'])

def test_verilator_run():
    import os.path
    import tempfile
    from fusesoc.utils import _import
    ref_dir_cc = os.path.join(ref_dir, 'cc')
    dummy_exe = 'V'+core.verilator.top_module

    work_root    = tempfile.mkdtemp()
    eda_api_file = os.path.join(ref_dir_cc, core.name.sanitized_name)+ '.eda.yml'
    backend = _import(tool, 'edatools')(eda_api_file=eda_api_file, work_root=work_root)
    shutil.copy(os.path.join(ref_dir, dummy_exe),
                os.path.join(work_root, dummy_exe))

    backend.run(params)

    compare_files(ref_dir, work_root, ['run.cmd'])
