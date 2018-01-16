import pytest

def test_empty_eda_api():
    import tempfile
    from fusesoc.main import _import

    (h, eda_api_file) = tempfile.mkstemp()

    with pytest.raises(RuntimeError):
        backend = _import('icarus')(eda_api_file=eda_api_file)

def test_incomplete_eda_api():
    import tempfile
    import yaml
    from fusesoc.main import _import

    (h, eda_api_file) = tempfile.mkstemp()
    contents = []
    
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'version' : '0.1.1'}))

    with pytest.raises(RuntimeError) as excinfo:
        backend = _import('icarus')(eda_api_file=eda_api_file)
    assert "Missing required parameter 'name'" in str(excinfo.value)

    with open(eda_api_file,'w') as f:
        f.write(yaml.dump({'version' : '0.1.1',
                           'name' : 'corename'}))

    backend = _import('icarus')(eda_api_file=eda_api_file)
