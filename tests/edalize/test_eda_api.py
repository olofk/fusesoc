import pytest
import shutil

def test_empty_eda_api():
    import tempfile
    from edalize import get_edatool

    (h, eda_api_file) = tempfile.mkstemp()

    with pytest.raises(TypeError):
        backend = get_edatool('icarus')(eda_api=None)

def test_incomplete_eda_api():
    from edalize import get_edatool

    with pytest.raises(RuntimeError) as excinfo:
        backend = get_edatool('icarus')(eda_api={'version' : '0.1.2'})
    assert "Missing required parameter 'name'" in str(excinfo.value)

    backend = get_edatool('icarus')(eda_api={
        'version' : '0.1.2',
        'name' : 'corename'})

def test_eda_api_files():
    from edalize import get_edatool
    files = [{'name' : 'plain_file'},
             {'name' : 'subdir/plain_include_file',
              'is_include_file' : True},
             {'name' : 'file_with_args',
              'file_type' : 'verilogSource',
              'logical_name' : 'libx'},
             {'name' : 'include_file_with_args',
              'is_include_file' : True,
              'file_type' : 'verilogSource',
              'logical_name' : 'libx'}]
    eda_api = {'files' : files,
               'name' : 'test_eda_api_files'}

    backend = get_edatool('icarus')(eda_api=eda_api)
    (parsed_files, incdirs) = backend._get_fileset_files()

    assert len(parsed_files) == 2
    assert parsed_files[0].name         == 'plain_file'
    assert parsed_files[0].file_type    == ''
    assert parsed_files[0].logical_name == ''
    assert parsed_files[1].name         == 'file_with_args'
    assert parsed_files[1].file_type    == 'verilogSource'
    assert parsed_files[1].logical_name == 'libx'

    assert incdirs == ['subdir', '.']

def test_eda_api_hooks():
    import os.path
    import tempfile
    from edalize import get_edatool

    tests_dir = os.path.dirname(__file__)
    ref_dir   = os.path.join(tests_dir, __name__)

    script = 'exit_1_script'
    hooks = {'pre_build' : [
        {'cmd' : ['sh', os.path.join(ref_dir, script)],
         'name' : script}]}

    work_root = tempfile.mkdtemp(prefix='eda_api_hooks_')
    eda_api = {'hooks' : hooks,
               'name' : script}

    backend = get_edatool('icarus')(eda_api=eda_api,
                                    work_root=work_root)
    with pytest.raises(RuntimeError):
        backend.build()
