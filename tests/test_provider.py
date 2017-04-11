import os
import pytest
import shutil

from test_common import get_core

def test_coregen_provider():
    core = get_core("coregencore")

    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    tests_dir = os.path.dirname(__file__)
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    core.setup()

    for f in ['dummy.cgp',
	      'dummy.xco',
	      os.path.join('subdir', 'dummy.extra')]:
        print(f)
        assert(os.path.isfile(os.path.join(core.files_root, f)))

    with open(os.path.join(core.files_root, 'run.cmd')) as f:
        assert(f.read() == '-r -b dummy.xco -p dummy.cgp\n')
    
def test_git_provider():
    core = get_core("gitcore")
    
    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    core.setup()

    for f in ['LICENSE',
	      'README.md',
	      'wb_common.core',
	      'wb_common.v',
	      'wb_common_params.v']:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

def test_github_provider():
    core = get_core("vlog_tb_utils")
    
    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    core.setup()
    
    for f in ['LICENSE',
              'vlog_functions.v',
              'vlog_tap_generator.v',
              'vlog_tb_utils.core',
              'vlog_tb_utils.v']:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

def test_logicore_provider():
    core = get_core("logicorecore")

    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    tests_dir = os.path.dirname(__file__)
    os.environ['PATH'] = os.path.join(tests_dir, 'mock_commands')+':'+os.environ['PATH']
    core.setup()

    for f in ['dummy.tcl',
	      'dummy.xci',
	      os.path.join('subdir', 'dummy.extra')]:
        assert(os.path.isfile(os.path.join(core.files_root, f)))

    with open(os.path.join(core.files_root, 'run.cmd')) as f:
        assert(f.read() == '-mode batch -source dummy.tcl\n')

def test_opencores_provider():
    core = get_core("opencorescore")

    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    core.setup()

    assert(os.path.isfile(os.path.join(core.files_root, 'tap_defines.v')))
    assert(os.path.isfile(os.path.join(core.files_root, 'tap_top.v')))

def test_url_provider():
    core = get_core("mmuart")

    if core.cache_status() is "downloaded":
        shutil.rmtree(core.files_root)
    core.setup()

    assert(os.path.isfile(os.path.join(core.files_root, 'uart_transceiver.v')))
