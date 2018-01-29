import pytest
import os.path
tests_dir = os.path.dirname(__file__)

def test_capi2_get_files():
    from fusesoc.core import Core


    core_file = os.path.join(tests_dir,
                             "capi2_cores",
                             "misc",
                             "files.core")
    core = Core(core_file, None, None)

    expected =  [
        {'is_include_file' : False,
         'file_type'       : 'user',
         'copyto'          : 'copied.file',
         'logical_name'    : '',
         'name'            : 'subdir/dummy.extra'},
        {'is_include_file' : False,
         'file_type'       : 'tclSource',
         'copyto'          : 'subdir/another.file',
         'logical_name'    : '',
         'name'            : 'dummy.tcl'},
        {'copyto'          : '',
         'file_type'       : 'verilogSource',
         'is_include_file' : True,
         'logical_name'    : '',
         'name'            : 'vlogfile'},
        {'copyto'          : '',
         'file_type'       : 'vhdlSource',
         'is_include_file' : False,
         'logical_name'    : '',
         'name'            : 'vhdlfile'},
        {'copyto'          : '',
         'file_type'       : 'user',
         'is_include_file' : False,
         'logical_name'    : '',
         'name'            : 'pickthisfile'},
        ]

    flags = {'tool' : 'icarus'}
    result = [vars(x) for x in core.get_files(flags)]
    assert expected == result

def test_capi2_get_tool_options():
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir,
                             "capi2_cores",
                             "misc",
                             "targets.core")
    core = Core(core_file, None, None)

    with pytest.raises(KeyError):
        core.get_tool_options({})

    assert {} == core.get_tool_options({'tool' : 'icarus'})
    flags = {'target'      : 'target_with_tool_options',
             'is_toplevel' : True}

    flags['tool'] = 'icarus'
    expected = {'iverilog_options' : ['a', 'few', 'options']}
    assert expected == core.get_tool_options(flags)

    flags['tool'] = 'vivado'
    expected = {'part' : 'xc7a35tcsg324-1'}
    assert expected == core.get_tool_options(flags)

def test_capi2_get_work_root():
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir,
                             "capi2_cores",
                             "misc",
                             "targets.core")
    core = Core(core_file, None, None)

    with pytest.raises(KeyError):
        core.get_work_root({})
    assert 'default-icarus'      == core.get_work_root({'tool' : 'icarus'})
    assert 'default-vivado'      == core.get_work_root({'tool' : 'vivado'})
    with pytest.raises(SyntaxError):
        core.get_work_root({'tool' : 'icarus', 'target' : 'invalid_target'})
    assert 'empty_target-icarus' == core.get_work_root({'tool' : 'icarus', 'target' : 'empty_target'})
