import pytest

def test_copyto():
    import os
    import tempfile

    from fusesoc.vlnv import Vlnv

    from test_common import common_cm

    flags = {'tool' : 'icarus'}

    work_root = tempfile.mkdtemp(prefix='copyto_')

    eda_api = common_cm.setup(Vlnv("copytocore"), flags, work_root, None)

    assert eda_api['files'] == [{'file_type': 'user',
                                 'logical_name': '',
                                 'name': 'copied.file',
                                 'is_include_file': False},
                                {'file_type': 'tclSource',
                                 'logical_name': '',
                                 'name': 'subdir/another.file',
                                 'is_include_file': False}]
    assert os.path.exists(os.path.join(work_root, 'copied.file'))
    assert os.path.exists(os.path.join(work_root, 'subdir', 'another.file'))
