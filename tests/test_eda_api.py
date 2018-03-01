import pytest
import shutil

def test_empty_eda_api():
    import tempfile
    from fusesoc.utils import _import

    (h, eda_api_file) = tempfile.mkstemp()

    with pytest.raises(RuntimeError):
        backend = _import('icarus', 'edatools')(eda_api_file=eda_api_file)

def test_incomplete_eda_api():
    import tempfile
    import yaml
    from fusesoc.utils import _import

    (h, eda_api_file) = tempfile.mkstemp()
    contents = []
    
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'version' : '0.1.2'}))

    with pytest.raises(RuntimeError) as excinfo:
        backend = _import('icarus', 'edatools')(eda_api_file=eda_api_file)
    assert "Missing required parameter 'name'" in str(excinfo.value)

    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'version' : '0.1.2',
                           'name' : 'corename'}))

    backend = _import('icarus', 'edatools')(eda_api_file=eda_api_file)

def test_eda_api_hooks():
    import os.path
    import tempfile
    import yaml
    from fusesoc.main import _import

    tests_dir = os.path.dirname(__file__)
    ref_dir   = os.path.join(tests_dir, __name__)

    script = 'exit_1_script'
    hooks = {'pre_build' : [
        {'cmd' : ['sh', os.path.join(ref_dir, script)],
         'name' : script}]}

    (h, eda_api_file) = tempfile.mkstemp(prefix='eda_api_hooks_')
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'hooks' : hooks,
                           'name' : script}))

    backend = _import('icarus', 'edatools')(eda_api_file=eda_api_file)
    with pytest.raises(RuntimeError):
        backend.build()

def test_eda_api_vpi():
    import os.path
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.vlnv import Vlnv

    tests_dir   = os.path.dirname(__file__)
    build_root  = tempfile.mkdtemp()
    cache_root  = os.path.join(tests_dir, 'cache')
    cores_root  = os.path.join(tests_dir, 'capi2_cores')
    work_root   = os.path.join(build_root, 'work')
    export_root = os.path.join(build_root, 'src')
    config = Config()
    config.build_root = build_root
    config.cache_root = cache_root
    cm = CoreManager(config)
    cm.add_cores_root(cores_root)
    eda_api = cm.setup(Vlnv("vpi"), {'tool' : 'icarus'}, work_root, export_root)
    expected = {'files'        : [],
                'hooks'        : {},
                'name'         : 'vpi_0',
                'parameters'   : [],
                'tool_options' : {'icarus': {}},
                'toplevel'     : 'not_used',
                'version'      : '0.1.2',
                'vpi'          : [{'src_files': ['../src/vpi_0/f1',
                                                 '../src/vpi_0/f3'],
                                   'include_dirs': ['../src/vpi_0/'],
                                   'libs': ['some_lib'],
                                   'name': 'vpi1'},
                                  {'src_files': ['../src/vpi_0/f4'],
                                   'include_dirs': [],
                                   'libs': [],
                                   'name': 'vpi2'}]

    }
    assert eda_api == expected
