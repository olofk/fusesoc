# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os.path
import warnings

import pytest

tests_dir = os.path.dirname(__file__)
cores_dir = os.path.join(tests_dir, "capi2_cores", "misc")


def test_files_out_of_hierarchy():
    import os
    import tempfile

    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(
        tests_dir,
        "capi2_cores",
        "files_out_of_hierarchy",
        "subdir",
        "files_out_of_hierarchy.core",
    )
    core = Core(Core2Parser(), core_file)
    export_root = tempfile.mkdtemp(prefix="capi2_files_out_of_hierarchy_")

    with pytest.warns(FutureWarning, match="not within the directory"):
        core.export(export_root, {"target": "bad", "is_toplevel": True})

    with warnings.catch_warnings(record=True) as record:
        core.export(export_root, {"target": "good", "is_toplevel": True})
        assert not record


def test_empty_core():
    import os
    import tempfile

    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "empty.core")
    with pytest.raises(SyntaxError) as excinfo:
        core = Core(Core2Parser(), core_file)
    assert "Error validating" in str(excinfo.value)


def test_virtual():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core
    from fusesoc.vlnv import Vlnv

    core_file = os.path.join(tests_dir, "capi2_cores", "virtual", "impl1.core")
    core = Core(Core2Parser(), core_file)
    assert core.get_virtuals() == [Vlnv("::someinterface:0")]


def test_capi2_export():
    import os
    import tempfile

    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "files.core")
    core = Core(Core2Parser(), core_file)

    export_root = tempfile.mkdtemp(prefix="capi2_export_")

    core.export(export_root)

    expected = [
        "dontpickthisfile",
        "dummy.tcl",
        "scriptfile",
        "subdir/dummy.extra",
        "vhdlfile",
        "vlogfile",
        "vpifile",
    ]
    result = []

    for root, dirs, files in os.walk(export_root):
        result += [os.path.relpath(os.path.join(root, f), export_root) for f in files]

    assert expected == sorted(result)

    with pytest.raises(RuntimeError) as excinfo:
        core.export(export_root, {"target": "will_fail", "is_toplevel": True})
    assert "Cannot find idontexist in" in str(excinfo.value)

    core.files_root = os.path.join(tests_dir, __name__)
    core.export(export_root, {"target": "files_root_test", "is_toplevel": True})
    expected = ["targets.info"]

    result = []

    for root, dirs, files in os.walk(export_root):
        result += [os.path.relpath(os.path.join(root, f), export_root) for f in files]
    assert expected == sorted(result)


def test_capi2_export_no_overwrite():
    import os
    import tempfile
    from filecmp import cmp

    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "files.core")
    core = Core(Core2Parser(), core_file)

    export_root = tempfile.mkdtemp(prefix="capi2_export_")

    expected = [
        "dontpickthisfile",
        "dummy.tcl",
        "scriptfile",
        "subdir/dummy.extra",
        "vhdlfile",
        "vlogfile",
        "vpifile",
    ]

    result = []

    # Export and check all dst files are equal to src files
    core.export(export_root)
    for f in expected:
        assert cmp(os.path.join(core.files_root, f), os.path.join(export_root, f))

    # Change one file in dst and...
    with open(os.path.join(export_root, "scriptfile"), "w") as f:
        f.write("Some random value")

    # ...verify that file is actually changed
    for f in expected:
        val = cmp(os.path.join(core.files_root, f), os.path.join(export_root, f))
        assert not val if f == "scriptfile" else val

    # Re-export and check for equality
    core.export(export_root)
    for f in expected:
        assert cmp(os.path.join(core.files_root, f), os.path.join(export_root, f))


def test_capi2_append():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core = Core(Core2Parser(), os.path.join(cores_dir, "append.core"))

    flags = {"is_toplevel": True}

    flags["target"] = "no_fs_no_fsappend"
    result = [x["name"] for x in core.get_files(flags)]
    expected = []
    assert expected == result

    flags["target"] = "no_fs_fsappend"
    result = [x["name"] for x in core.get_files(flags)]
    expected = ["file3", "file4"]
    assert expected == result

    flags["target"] = "fs_no_fsappend"
    result = [x["name"] for x in core.get_files(flags)]
    expected = ["file1", "file2"]
    assert expected == result

    flags["target"] = "fs_fsappend"
    result = [x["name"] for x in core.get_files(flags)]
    expected = ["file1", "file2", "file3", "file4"]
    assert expected == result


def test_capi2_get_depends():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core
    from fusesoc.vlnv import Vlnv

    core = Core(
        Core2Parser(), os.path.join(tests_dir, "capi2_cores", "misc", "depends.core")
    )
    flags = {}
    result = core.get_depends(flags)

    expected = [
        Vlnv("unversioned"),
        Vlnv("versioned-1.0"),
        Vlnv("<lt-1.0"),
        Vlnv("<=lte-1.0"),
        Vlnv("=eq-1.0"),
        Vlnv(">gt-1.0"),
        Vlnv(">=gte-1.0"),
        Vlnv("::n"),
        Vlnv("::nv:1.0"),
        Vlnv(":l:nv:1.0"),
        Vlnv("v:l:nv:1.0"),
        Vlnv("<::vlnvlt:1.0"),
        Vlnv("<=::vlnvlte:1.0"),
        Vlnv("=::vlnveq:1.0"),
        Vlnv(">::vlnvgt:1.0"),
        Vlnv(">=::vlnvgte:1.0"),
        Vlnv("^::vlnvmajor:1.0"),
        Vlnv("~::vlnvminor:2.2.3"),
    ]
    assert len(result) == len(expected)
    for i in range(len(result)):
        assert result[i] == expected[i]


def test_capi2_get_files():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "files.core")
    core = Core(Core2Parser(), core_file)

    expected = [
        {
            "file_type": "vhdlSource",
            "logical_name": "overridden_logical_name",
            "name": "vlogfile",
        },
        {
            "file_type": "vhdlSource",
            "logical_name": "default_logical_name",
            "name": "vhdlfile",
        },
        {
            "file_type": "user",
            "copyto": "copied.file",
            "name": "subdir/dummy.extra",
        },
        {
            "file_type": "tclSource",
            "copyto": "subdir/another.file",
            "name": "dummy.tcl",
        },
        {
            "file_type": "verilogSource",
            "is_include_file": True,
            "name": "vlogfile",
        },
        {
            "file_type": "vhdlSource",
            "name": "vhdlfile",
        },
        {
            "file_type": "user",
            "name": "pickthisfile",
        },
    ]

    flags = {"tool": "icarus"}
    result = core.get_files(flags)

    assert expected == result

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "fileattrs.core")
    core = Core(Core2Parser(), core_file)
    flags = {"is_toplevel": True, "target": "defines"}
    result = core.get_files(flags)
    expected = [
        {"name": "hasdefines", "define": {"key1": "value1", "key2": "value2"}},
        {
            "name": "nodefines",
        },
    ]
    assert expected == result


def test_capi2_type_check():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "typecheck.core")

    with pytest.raises(SyntaxError) as excinfo:
        core = Core(Core2Parser(), core_file)
    assert "Error validating" in str(excinfo.value)


def test_capi2_get_filters():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core = Core(Core2Parser(), os.path.join(cores_dir, "filters.core"))
    assert [] == core.get_filters({"is_toplevel": True, "target": "nofilters"})
    assert [] == core.get_filters({"is_toplevel": True, "target": "emptyfilters"})
    assert ["corefilter1", "corefilter2"] == core.get_filters(
        {"is_toplevel": True, "target": "filters"}
    )


def test_capi2_get_flags():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core = Core(Core2Parser(), os.path.join(cores_dir, "flags.core"))

    with pytest.raises(RuntimeError) as e:
        core.get_flags("bad_target")
    assert "::flags:0' has no target 'bad_target'" in str(e.value)
    assert {} == core.get_flags("noflags")
    assert {} == core.get_flags("emptyflags")
    assert {"tool": "mytool"} == core.get_flags("emptyflagstool")
    expected = {"flag1": False, "flag2": True, "flag3": True}
    assert expected == core.get_flags("allflags")
    expected["tool"] = "mytool"
    expected.pop("flag3")
    assert expected == core.get_flags("allflagstool")


def test_capi2_get_generators():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core = Core(Core2Parser(), os.path.join(cores_dir, "generate", "generators.core"))

    generators = core.get_generators()
    assert len(generators) == 2
    assert generators["generator1"]["command"] == "testgen.py"
    assert generators["generator2"]["command"] == "testgen.py"
    assert generators["generator2"]["cache_type"] == "input"
    assert generators["generator2"]["file_input_parameters"] == "file_in_param1"


def test_capi2_get_parameters():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "parameters.core")
    core = Core(Core2Parser(), core_file)

    param1 = {
        "datatype": "str",
        "paramtype": "vlogparam",
    }
    param2 = {
        "datatype": "str",
        "default": "default_value",
        "description": "This is a parameter",
        "paramtype": "vlogparam",
    }
    intparam = {
        "datatype": "int",
        "default": 5446,
        "paramtype": "vlogparam",
    }
    boolfalse = {
        "datatype": "bool",
        "default": False,
        "paramtype": "vlogparam",
    }

    booltrue = {
        "datatype": "bool",
        "default": True,
        "paramtype": "vlogparam",
    }
    int0 = {
        "datatype": "int",
        "default": 0,
        "paramtype": "vlogparam",
    }
    emptystr = {
        "datatype": "str",
        "paramtype": "vlogparam",
    }
    realpi = {
        "datatype": "real",
        "default": 3.14159,
        "paramtype": "vlogparam",
    }

    flags = {"is_toplevel": True}
    expected = {"param1": param1}

    assert expected == core.get_parameters(flags)

    flags["target"] = "noparameters"
    expected = {}
    assert expected == core.get_parameters(flags)

    flags["target"] = "nonexistant"
    with pytest.raises(SyntaxError) as excinfo:
        core.get_parameters(flags)
    assert (
        "Parameter 'idontexist', requested by target 'nonexistant', was not found"
        in str(excinfo.value)
    )

    flags["target"] = "multiparameters"
    expected = {"param1": param1, "param2": param2}
    assert expected == core.get_parameters(flags)

    flags["target"] = "use_flags"
    expected = {
        "param2": param2,
        "condparamtype": {"datatype": "str", "paramtype": "vlogparam"},
    }

    assert expected == core.get_parameters(flags)

    flags["tool"] = "icarus"
    expected = {
        "param1": param1,
        "condparamtype": {"datatype": "str", "paramtype": "plusarg"},
    }
    assert expected == core.get_parameters(flags)

    flags["target"] = "types"
    expected = {
        "param2": param2,
        "intparam": intparam,
        "boolfalse": boolfalse,
        "booltrue": booltrue,
        "realpi": realpi,
    }
    result = core.get_parameters(flags)
    assert expected == result
    assert str == type(result["param2"]["datatype"])
    assert str == type(result["param2"]["default"])
    assert str == type(result["param2"]["description"])
    assert str == type(result["param2"]["paramtype"])
    assert int == type(result["intparam"]["default"])
    assert bool == type(result["boolfalse"]["default"])
    assert bool == type(result["booltrue"]["default"])
    assert float == type(result["realpi"]["default"])

    flags["target"] = "empty"
    expected = {"int0": int0, "emptystr": emptystr}

    assert expected == core.get_parameters(flags)

    flags["target"] = "override"
    param1["default"] = "def"
    param2["default"] = "new_def"
    intparam["default"] = 0xDEADBEEF
    boolfalse["default"] = True
    booltrue["default"] = False
    realpi["default"] = 3.14
    expected = {
        "param1": param1,
        "param2": param2,
        "intparam": intparam,
        "boolfalse": boolfalse,
        "booltrue": booltrue,
        "realpi": realpi,
    }
    assert expected == core.get_parameters(flags)


def test_capi2_get_scripts():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    simple1 = {
        "cmd": ["simple_cmd1"],
        "env": {"FILES_ROOT": "my_files_root"},
        "name": "simple1",
    }
    simple2 = {
        "cmd": ["simple_cmd2"],
        "env": {"FILES_ROOT": "my_files_root"},
        "name": "simple2",
    }
    simple3 = {
        "cmd": ["simple_cmd3"],
        "env": {"FILES_ROOT": "my_files_root"},
        "name": "simple3",
    }
    simple4 = {
        "cmd": ["simple_cmd4"],
        "env": {"FILES_ROOT": "my_files_root"},
        "name": "simple4",
    }
    with_env = {
        "cmd": ["simple5"],
        "env": {"FILES_ROOT": "my_files_root", "TESTENV": "testvalue"},
        "name": "with_env",
    }
    multi_cmd = {
        "cmd": ["command", "with", "args"],
        "env": {"FILES_ROOT": "my_files_root"},
        "name": "multi_cmd",
    }
    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "hooks.core")
    core = Core(Core2Parser(), core_file)

    flags = {"is_toplevel": True}
    expected = {"pre_build": [simple1]}
    assert expected == core.get_scripts("my_files_root", flags)

    flags["target"] = "nohooks"
    expected = {}
    assert expected == core.get_scripts("my_files_root", flags)

    flags["target"] = "nonexistant"
    with pytest.raises(SyntaxError) as excinfo:
        core.get_scripts("", flags)
    assert (
        "Script 'idontexist', requested by target 'nonexistant', was not found"
        in str(excinfo.value)
    )

    flags["target"] = "allhooks"
    expected = {
        "pre_build": [simple1],
        "post_build": [simple2],
        "pre_run": [simple3],
        "post_run": [simple4],
    }
    assert expected == core.get_scripts("my_files_root", flags)

    flags["target"] = "multihooks"
    expected = {"pre_run": [simple1, with_env, multi_cmd]}
    assert expected == core.get_scripts("my_files_root", flags)

    flags["target"] = "use_flags"
    expected = {"post_run": [simple2]}
    assert expected == core.get_scripts("my_files_root", flags)

    flags["tool"] = "icarus"
    expected = {"post_run": [simple1]}
    assert expected == core.get_scripts("my_files_root", flags)


def test_capi2_get_tool_options():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "targets.core")
    core = Core(Core2Parser(), core_file)

    with pytest.raises(KeyError):
        core.get_tool_options({})

    assert {} == core.get_tool_options({"tool": "icarus"})
    flags = {"target": "target_with_tool_options", "is_toplevel": True}

    flags["tool"] = "icarus"
    expected = {"iverilog_options": ["a", "few", "options"]}
    assert expected == core.get_tool_options(flags)

    flags["tool"] = "vivado"
    expected = {"part": "xc7a35tcsg324-1"}
    assert expected == core.get_tool_options(flags)

    flags["tool"] = "invalid"
    expected = {}
    assert expected == core.get_tool_options(flags)


def test_capi2_get_toplevel():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "toplevel.core")
    core = Core(Core2Parser(), core_file)

    flags = {"target": "no_toplevel"}
    with pytest.raises(SyntaxError):
        core.get_toplevel(flags)

    flags = {"target": "str_toplevel"}
    assert "toplevel_as_string" == core.get_toplevel(flags)

    flags = {"target": "list_toplevel"}
    assert "toplevel as list" == core.get_toplevel(flags)


def test_capi2_get_ttptttg():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core = Core(Core2Parser(), os.path.join(cores_dir, "generate", "generate.core"))

    flags = {"is_toplevel": True}
    expected = [
        {
            "name": "testgenerate_without_params",
            "generator": "generator1",
            "pos": "append",
            "config": {},
        },
        {
            "name": "testgenerate_with_params",
            "generator": "generator1",
            "pos": "append",
            "config": {"param1": "a param", "param2": ["list", "of", "stuff"]},
        },
        {
            "name": "testgenerate_with_override",
            "generator": "generator1",
            "pos": "append",
            "config": {"the_value": 138},
        },
        {
            "name": "testgenerate_with_cache",
            "generator": "generator2",
            "pos": "append",
            "config": {"file_in_param1": "file_cachetest"},
        },
    ]
    assert expected == core.get_ttptttg(flags)

    flags["target"] = "nogenerate"
    assert [] == core.get_ttptttg(flags)

    flags["target"] = "invalid_generate"
    with pytest.raises(SyntaxError) as excinfo:
        core.get_ttptttg(flags)
    assert (
        "Generator instance 'idontexist', requested by target 'invalid_generate', was not found"
        in str(excinfo.value)
    )

    flags["target"] = "invalid_target"
    assert [] == core.get_ttptttg(flags)


def test_capi2_get_vpi():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "vpi.core")
    core = Core(Core2Parser(), core_file)

    expected = [
        {
            "src_files": ["f1", "f3"],
            "include_dirs": [""],
            "libs": ["some_lib"],
            "name": "vpi1",
        },
        {"src_files": ["f4"], "include_dirs": [], "libs": [], "name": "vpi2"},
    ]

    assert [] == core.get_vpi({"is_toplevel": True, "target": "invalid"})
    assert expected == core.get_vpi({"is_toplevel": True})
    assert expected == core.get_vpi({"is_toplevel": False})


def test_capi2_info():
    from fusesoc.capi2.coreparser import Core2Parser
    from fusesoc.core import Core

    dirs_and_corenames = [("", "targets"), ("generate", "generators")]

    for subdir, core_name in dirs_and_corenames:
        core_file = os.path.join(
            tests_dir, "capi2_cores", "misc", subdir, core_name + ".core"
        )
        core = Core(Core2Parser(), core_file)

        gen_info = "\n".join(
            [
                x
                for x in core.info().split("\n")
                if not any([y in x for y in ["Core root", "Core file"]])
            ]
        )
        with open(os.path.join(tests_dir, __name__, core_name + ".info")) as f:
            assert f.read() == gen_info, core_name


def test_core2parser():
    import os
    import tempfile

    from fusesoc.capi2.coreparser import Core2Parser

    core_file = os.path.join(
        tests_dir, "capi2_cores", "parser", "no_additional_properties.core"
    )

    parser = Core2Parser(allow_additional_properties=False)
    assert parser.get_version() == 2
    assert parser.get_allow_additional_properties() == False
    assert parser.get_preamble() == "CAPI=2:"

    expected = {
        "name": "::noadditionalproperties:0",
        "filesets": {
            "somename": {
                "files": ["somefile1", {"someincludefile1": {"is_include_file": True}}]
            }
        },
        "targets": {"default": {"filesets": ["somename"]}},
    }

    capi2_data = parser.read(core_file)
    assert expected == capi2_data

    tmpfile = tempfile.mktemp(prefix="capi2_parser_")
    parser.write(tmpfile, capi2_data)
    capi2_readback_data = parser.read(tmpfile)
    os.remove(tmpfile)
    assert capi2_data == capi2_readback_data

    capi2_data["mycustomprop1"] = {
        "one": "mystring",
        "two": ["list_item_1", "list_item_2"],
    }

    with pytest.raises(SyntaxError) as excinfo:
        parser.write(tmpfile, capi2_data)
    assert "Error validating" in str(excinfo.value)

    core_file = os.path.join(
        tests_dir, "capi2_cores", "parser", "with_additional_properties.core"
    )

    with pytest.raises(SyntaxError) as excinfo:
        parser.read(core_file)
    assert "Error validating" in str(excinfo.value)

    parser = Core2Parser(allow_additional_properties=True)
    assert parser.get_allow_additional_properties() == True

    expected = {
        "name": "::withadditionalproperties:0",
        "filesets": {
            "somename": {
                "files": ["somefile1", {"someincludefile1": {"is_include_file": True}}],
                "mycustomprop1": "this is a custom property",
                "mycustomprop2": 1,
            }
        },
        "targets": {"default": {"filesets": ["somename"]}},
        "mycustomprop3": {
            "subitem1": "mystring",
            "subitem2": ["list_item_1", "list_item_2"],
        },
    }

    capi2_data = parser.read(core_file)
    assert expected == capi2_data

    capi2_data["mycustomprop4"] = "new string"
    parser.write(tmpfile, capi2_data)
    capi2_readback_data = parser.read(tmpfile)
    os.remove(tmpfile)
    assert capi2_data == capi2_readback_data


def test_syntax_error():
    from fusesoc.capi2.coreparser import Core2Parser

    core_file = os.path.join(tests_dir, "capi2_cores", "misc", "syntax_error.core")

    parser = Core2Parser()
    with pytest.raises(SyntaxError) as excinfo:
        parser.read(core_file)
    assert "did not find expected node content" in str(excinfo.value)


def test_inheritance():
    import os

    from fusesoc.capi2.coreparser import Core2Parser

    core_file = os.path.join(tests_dir, "capi2_cores", "parser", "inheritance.core")

    parser = Core2Parser()
    assert parser.get_version() == 2
    assert parser.get_preamble() == "CAPI=2:"

    expected = {
        "name": "::inheritance:0",
        "filesets": {
            "fileset_a": {"files": ["1.txt", "2.txt", "3.txt"]},
            "fileset_b": {"files": ["4.txt", "5.txt", "6.txt"]},
            "fileset_c": {"files": ["7.txt", "8.txt", "9.txt"]},
        },
        "targets": {
            "default": {"filesets": ["fileset_a"]},
            "child": {"filesets": ["fileset_a"], "filesets_append": ["fileset_b"]},
            "grandchild": {
                "filesets": ["fileset_a"],
                "filesets_append": ["fileset_b", "fileset_c"],
            },
            "child2": {"filesets": ["fileset_b"], "filesets_append": ["fileset_c"]},
            "subfield": {
                "tools": {
                    "verilator": {"mode": "cc", "verilator_options": ["--timing"]}
                }
            },
            "subfield_child": {
                "tools": {
                    "verilator": {
                        "mode": "lint-only",
                        "verilator_options": ["--timing"],
                    }
                }
            },
            "merge_test1": {"filesets": ["fileset_a"]},
            "merge_test2<<": {"tools": {"2<<": {}}},
            "<<merge_test3": {"tools": {"<<3": {}}},
            "merge_test4": {
                "tools": {"t4": {"t44": "<<4", "filesets": ["fileset_a"]}},
                "filesets": ["fileset_a"],
            },
            "merge_test5": {"filesets": ["fileset_a"]},
        },
    }

    capi2_data = parser.read(core_file)
    assert expected == capi2_data
