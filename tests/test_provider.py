import os
import pytest
import shutil
import tempfile

from fusesoc.core import Core

from test_common import tests_dir

cores_root = os.path.join(tests_dir, 'cores')

def test_coregen_provider():

    cache_root = tempfile.mkdtemp('coregen_')
    core = Core(os.path.join(cores_root, 'misc', 'coregencore.core'), cache_root)

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    core.setup()

    for f in ['dummy.cgp',
	      'dummy.xco',
	      os.path.join('subdir', 'dummy.extra')]:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

    with open(os.path.join(core.files_root, 'run.cmd')) as f:
        assert(f.read() == '-r -b dummy.xco -p dummy.cgp\n')
    
def test_git_provider():
    cache_root = tempfile.mkdtemp('git_')
    core = Core(os.path.join(cores_root, 'misc', 'gitcore.core'), cache_root)
    
    core.setup()

    for f in ['LICENSE',
	      'README.md',
	      'wb_common.core',
	      'wb_common.v',
	      'wb_common_params.v']:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

def test_github_provider():
    cache_root = tempfile.mkdtemp('github_')
    core = Core(os.path.join(cores_root, 'vlog_tb_utils', 'vlog_tb_utils-1.1.core'), cache_root)
    
    core.setup()
    
    for f in ['LICENSE',
              'vlog_functions.v',
              'vlog_tap_generator.v',
              'vlog_tb_utils.core',
              'vlog_tb_utils.v']:
        assert(os.path.isfile(os.path.join(core.files_root, f)))
        ref_dir   = os.path.join(os.path.dirname(__file__),  __name__)
        f = 'vlog_functions.v'
    with open(os.path.join(ref_dir, f)) as fref, open(os.path.join(core.files_root, f)) as fgen:
            assert fref.read() == fgen.read(), f

def test_logicore_provider():

    cache_root = tempfile.mkdtemp('logicore_')
    core = Core(os.path.join(cores_root, 'misc', 'logicorecore.core'), cache_root)

    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    core.setup()

    for f in ['dummy.tcl',
	      'dummy.xci',
	      os.path.join('subdir', 'dummy.extra')]:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

    with open(os.path.join(core.files_root, 'vivado.cmd')) as f:
        assert(f.read() == '-mode batch -source dummy.tcl\n')

def test_opencores_provider():
    cache_root = tempfile.mkdtemp('opencores_')
    core = Core(os.path.join(cores_root, 'misc', 'opencorescore.core'), cache_root)

    core.setup()

    assert(os.path.isfile(os.path.join(core.files_root, 'tap_defines.v')))
    assert(os.path.isfile(os.path.join(core.files_root, 'tap_top.v')))

def test_url_provider():
    cores_root = os.path.join(tests_dir, 'capi2_cores', 'providers')

    for corename in ['url_simple',
                     'url_simple_with_user_agent',
                     'url_tar',
                     'url_zip']:
        cache_root = tempfile.mkdtemp(prefix='url_')
        core = Core(os.path.join(cores_root, corename+'.core'), cache_root)
        core.setup()
        assert(os.path.isfile(os.path.join(core.files_root, 'file.v')))
