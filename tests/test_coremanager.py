import os
import pytest
import shutil

from fusesoc.coremanager import CoreManager
from test_common import get_core

def test_copyto():
    tests_dir = os.path.dirname(__file__)
    core      = get_core("copytocore")
    flags = {'tool' : 'icarus'}
    
    export_root = None
    work_root   = os.path.join(tests_dir,
                               'build',
                               core.name.sanitized_name,
                               core.get_work_root(flags))
    if os.path.exists(work_root):
        for f in os.listdir(work_root):
            if os.path.isdir(os.path.join(work_root, f)):
                shutil.rmtree(os.path.join(work_root, f))
            else:
                os.remove(os.path.join(work_root, f))
    else:
        os.makedirs(work_root)

    eda_api = CoreManager().setup(core.name, flags, work_root, None)

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
