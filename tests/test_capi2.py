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

def test_capi2_get_scripts():
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir,
                             "capi2_cores",
                             "misc",
                             "hooks.core")
    core = Core(core_file, None, None)

    flags    = {'is_toplevel' : True}
    expected = {'pre_build' : [{'cmd' : ['simple_cmd1'],
                                'env' : {},
                                'name' : 'simple1'}]}
    assert expected == core.get_scripts("", flags)

    flags['target'] = 'nohooks'
    expected = {}
    assert expected == core.get_scripts("", flags)

    flags['target'] = 'nonexistant'
    with pytest.raises(SyntaxError) as excinfo:
        core.get_scripts("", flags)
    assert "Script 'idontexist', requested by target 'nonexistant', was not found" in str(excinfo.value)

    flags['target'] = 'allhooks'
    expected = {
        'pre_build'  : [{'cmd'  : ['simple_cmd1'],
                         'env'  : {},
                         'name' : 'simple1'}],
        'post_build' : [{'cmd'  : ['simple_cmd2'],
                         'env'  : {},
                         'name' : 'simple2'}],
        'pre_run'    : [{'cmd'  : ['simple_cmd3'],
                         'env'  : {},
                         'name' : 'simple3'}],
        'post_run'   : [{'cmd'  : ['simple_cmd4'],
                         'env'  : {},
                         'name' : 'simple4'}],
        }
    assert expected == core.get_scripts("", flags)

    flags['target'] = 'multihooks'
    expected = {
        'pre_run'  : [{'cmd'  : ['simple_cmd1'],
                       'env'  : {},
                       'name' : 'simple1'},
                      {'cmd'  : ['simple5'],
                       'env'  : {'TESTENV' : 'testvalue'},
                       'name' : 'with_env'},
                      {'cmd'  : ['command', 'with', 'args'],
                       'env'  : {},
                       'name' : 'multi_cmd'}]
        }
    assert expected == core.get_scripts("", flags)

    flags['target'] = 'use_flags'
    expected = {'post_run' : [{'cmd' : ['simple_cmd2'],
                               'env' : {},
                               'name' : 'simple2'}]}
    assert expected == core.get_scripts("", flags)

    flags['tool'] = 'icarus'
    expected = {'post_run' : [{'cmd' : ['simple_cmd1'],
                               'env' : {},
                               'name' : 'simple1'}]}
    assert expected == core.get_scripts("", flags)

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

def test_capi2_info():
    from fusesoc.core import Core
    for core_name in ['targets']:
        core_file = os.path.join(tests_dir,
                                 "capi2_cores",
                                 "misc",
                                 core_name+'.core')
        core = Core(core_file, None, None)

        gen_info = '\n'.join([x for x in core.info().split('\n') if not 'Core root' in x])
        with open(os.path.join(tests_dir, __name__, core_name+".info")) as f:
            assert f.read() == gen_info, core_name
