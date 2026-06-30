# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import shlex
from pathlib import Path

import pytest


def test_apply_filters(caplog):
    from fusesoc.edalizer import Edalizer

    input_edam = {
        "files": [
            {"name": "qip_file.qip", "file_type": "QIP"},
            {"name": "sv_file.sv"},
            {"name": "tcl_file.tcl"},
            {"name": "vlog_file.v"},
            {"name": "vlog05_file.v", "file_type": "verilogSource-2005"},
            {"name": "vlog_incfile.v", "is_include_file": True},
        ],
        "filters": ["autotype"],
    }
    ref_edam = {
        "files": [
            {"name": "qip_file.qip", "file_type": "QIP"},
            {"name": "sv_file.sv", "file_type": "systemVerilogSource"},
            {"name": "tcl_file.tcl", "file_type": "tclSource"},
            {"name": "vlog_file.v", "file_type": "verilogSource"},
            {"name": "vlog05_file.v", "file_type": "verilogSource-2005"},
            {
                "name": "vlog_incfile.v",
                "file_type": "verilogSource",
                "is_include_file": True,
            },
        ],
        "filters": ["autotype"],
    }

    # Filter from core
    edalizer = Edalizer(
        toplevel=None,
        flags=None,
        work_root=None,
        core_manager=None,
    )
    edalizer.edam = input_edam
    edalizer.apply_filters([])
    assert edalizer.edam == ref_edam

    # No filters
    edalizer.edam = {}
    edalizer.apply_filters([])
    assert edalizer.edam == {}

    # Non-existent filter
    edalizer.edam = {}

    with pytest.raises(RuntimeError) as excinfo:
        edalizer.apply_filters(["doesnotexist"])

    assert "Could not find EDAM filter 'doesnotexist'" in str(excinfo.value)
    assert edalizer.edam == {}


def test_tool_or_flow():
    import os

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    tests_dir = os.path.dirname(__file__)
    cores_dir = os.path.join(tests_dir, "capi2_cores", "misc")

    lib = Library("edalizer", cores_dir)

    cm = CoreManager(Config())
    cm.add_library(lib, [])

    core = cm.get_core(Vlnv("::flow"))

    ref_edam = {
        "version": "0.2.1",
        "cores": {
            "::flow:0": {
                "core_file": "tests/capi2_cores/misc/flow.core",
                "dependencies": [],
                "license": None,
            }
        },
        "dependencies": {"::flow:0": []},
        "files": [],
        "filters": [],
        "hooks": {},
        "name": "flow_0",
        "parameters": {},
        "toplevel": "unused",
        "vpi": [],
        "flow_options": {},
    }

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "nothing"},
        core_manager=cm,
        work_root=".",
    ).run()
    assert edam == ref_edam

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "flowonly"},
        core_manager=cm,
        work_root=".",
    ).run()
    assert edam == ref_edam

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "emptyflowoptions"},
        core_manager=cm,
        work_root=".",
    ).run()
    assert edam == ref_edam

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "toolonly"},
        core_manager=cm,
        work_root=".",
    ).run()
    assert edam == ref_edam

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "flowandtool"},
        core_manager=cm,
        work_root=".",
    ).run()
    assert edam == ref_edam

    edam = Edalizer(
        toplevel=core.name,
        flags={"target": "flowoptions"},
        core_manager=cm,
        work_root=".",
    ).run()

    ref_edam["flow_options"] = {
        "tool1": {"someoption": "somevalue"},
        "tool2": {"otheroption": ["detroit", 442]},
    }
    assert edam == ref_edam


def test_generators():
    import shutil
    import tempfile
    from pathlib import Path

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    tests_dir = Path(__file__).parent
    cores_dir = tests_dir / "capi2_cores" / "misc" / "generate"

    lib = Library("edalizer", cores_dir)

    cm = CoreManager(Config())
    cm.add_library(lib, [])

    core = cm.get_core(Vlnv("::generate"))

    build_root = Path(tempfile.mkdtemp(prefix="export_"))
    export_root = build_root / "exported_files"

    edalizer = Edalizer(
        toplevel=core.name,
        flags={"tool": "icarus"},
        core_manager=cm,
        work_root=build_root / "work",
        export_root=export_root,
        system_name=None,
    )
    edalizer.run()

    ref_edam = {
        "version": "0.2.1",
        "name": "generate_0",
        "cores": {
            "::generators:0": {
                "core_file": "generators.core",
                "dependencies": [],
                "license": None,
            },
            "::generate:0": {
                "core_file": "generate.core",
                "dependencies": [
                    "::generators:0",
                    "::generate-testgenerate_without_params:0",
                    "::generate-testgenerate_with_params:0",
                    "::generate-testgenerate_with_override:0",
                    "::generate-testgenerate_with_cache:0",
                    "::generate-testgenerate_with_file_cache:0",
                ],
                "license": "MIT",
            },
            "::generate-testgenerate_without_params:0": {
                "core_file": "generated.core",
                "dependencies": [],
                "license": None,
            },
            "::generate-testgenerate_with_params:0": {
                "core_file": "generated.core",
                "dependencies": [],
                "license": None,
            },
            "::generate-testgenerate_with_override:0": {
                "core_file": "generated.core",
                "dependencies": [],
                "license": None,
            },
            "::generate-testgenerate_with_cache:0": {
                "core_file": "generated.core",
                "dependencies": [],
                "license": None,
            },
            "::generate-testgenerate_with_file_cache:0": {
                "core_file": "generated.core",
                "dependencies": [],
                "license": None,
            },
        },
        "toplevel": "na",
        "dependencies": {
            "::generators:0": [],
            "::generate:0": [
                "::generators:0",
                "::generate-testgenerate_without_params:0",
                "::generate-testgenerate_with_params:0",
                "::generate-testgenerate_with_override:0",
                "::generate-testgenerate_with_cache:0",
                "::generate-testgenerate_with_file_cache:0",
            ],
            "::generate-testgenerate_without_params:0": [],
            "::generate-testgenerate_with_params:0": [],
            "::generate-testgenerate_with_override:0": [],
            "::generate-testgenerate_with_cache:0": [],
            "::generate-testgenerate_with_file_cache:0": [],
        },
        "parameters": {"p": {"datatype": "str", "paramtype": "vlogparam"}},
        "tool_options": {"icarus": {}},
        "flow_options": {},
        "hooks": {},
        "files": [],
        "filters": [],
        "vpi": [],
    }

    # EDAM will contain absolute paths to core files that are non-deterministic.
    # Remove these before comparing and only keep the name of the core file
    for core in edalizer.edam["cores"].values():
        core["core_file"] = Path(core["core_file"]).name
    assert ref_edam == edalizer.edam

    name_to_core = {str(core.name): core for core in edalizer.cores}
    for flavour in ["testgenerate_with_params", "testgenerate_without_params"]:
        core_name = f"::generate-{flavour}:0"
        assert core_name in name_to_core
        core = name_to_core[core_name]

    # Test generator input without file_input_params
    core_name = "::generate-testgenerate_with_cache:0"
    assert core_name in name_to_core
    core = name_to_core[core_name]

    core_root = Path(core.core_root)
    assert core_root.is_dir()
    assert (
        core_root.name
        == "generate-testgenerate_with_cache_0-616d6cf151dba72fcd893c08a8e18e6dba2b81ee25dec08c92e0177064dfc18c"
    )
    shutil.rmtree(core.core_root, ignore_errors=True)

    # Test generator input file_input_params
    core_name = "::generate-testgenerate_with_file_cache:0"
    assert core_name in name_to_core
    core = name_to_core[core_name]
    core_root = Path(core.core_root)

    assert core_root.is_dir()
    assert (
        core_root.name
        == "da265f9dccc9d9e64d059f677508f9550b403c99e6ce5df07c6fb1d711d0ee99"
    )
    assert (
        core_root.parent.name
        == "generate-testgenerate_with_file_cache_0-f3d9e1e462ef1f7113fafbacd62d6335dd684e69332f75498fb01bfaaa7c11ee"
    )
    shutil.rmtree(core.core_root, ignore_errors=True)


def test_hook_script_names_are_unique_per_core():
    """Two cores with a same-named hook script must produce distinct EDAM
    hook names so edalize doesn't generate duplicate Makefile targets.

    Regression test for https://github.com/olofk/fusesoc/issues/646
    """
    import os

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    tests_dir = os.path.dirname(__file__)
    cores_dir = os.path.join(tests_dir, "capi2_cores", "hooks_collision")

    cm = CoreManager(Config())
    cm.add_library(Library("hooks_collision", cores_dir), [])

    child = cm.get_core(Vlnv("::hookcollision-child:0"))
    edam = Edalizer(
        toplevel=child.name,
        flags={"tool": "icarus"},
        core_manager=cm,
        work_root=".",
    ).run()

    pre_build_hooks = edam["hooks"]["pre_build"]
    assert len(pre_build_hooks) == 2
    names = [h["name"] for h in pre_build_hooks]
    assert len(set(names)) == 2, f"hook script names collided: {names}"
    assert "hookcollision-parent_0_myhook" in names
    assert "hookcollision-child_0_myhook" in names


@pytest.mark.parametrize(
    "datatype,value",
    (
        ("bool", None),
        ("bool", "FalSE"),
        ("bool", "f"),
        ("bool", "No"),
        ("bool", "n"),
        ("bool", "0"),
        ("bool", "tRuE"),
        ("bool", "t"),
        ("bool", "Yes"),
        ("bool", "y"),
        ("bool", "1"),
        ("int", None),
        ("int", -2137),
        ("int", 0),
        ("int", 2137),
        ("real", None),
        ("real", -0.25),
        ("real", 0.0),
        ("real", 0.25),
        ("str", None),
        ("str", ""),
        ("str", "arg"),
        ("str", "arg with spaces"),
        ("list", None),
        ("list", ""),
        ("list", "-arg1"),
        ("list", "-arg1 val1"),
        ("list", "-arg1 val1 -arg2"),
        ("list", "-arg1 val1 -arg2 val2"),
        ("list", "-arg1 val1 -arg2 'val2 with single quote'"),
        ("list", '-arg1 val1 -arg2 "val2 with double quote"'),
        ("file", None),
        ("file", "input.tcl"),
    ),
)
def test_edalizer_parse_args_for_options(datatype: str, value: object) -> None:
    """Test parsing arguments for options by the Edalizer class."""
    from edalize.flows.edaflow import Edaflow

    from fusesoc.edalizer import Edalizer

    name = f"my_{datatype}_option"

    class MyFlow(Edaflow):
        argtypes = []

        FLOW_OPTIONS = {
            name: {"type": datatype, "desc": "Description"},
        }

    edalizer = Edalizer(
        toplevel=None,
        flags=None,
        work_root=None,
        core_manager=None,
    )

    edalizer.edam = {
        "name": "flow",
        "flow_options": {},
        "parameters": {},
    }

    backendargs: list[str]

    if value is None:
        backendargs = [f"--{name}"] if datatype == "bool" else []
    elif datatype == "list":
        # To pass arguments with leading dashes to backend
        backendargs = [f"--{name}={value}"]
    else:
        backendargs = [f"--{name}", str(value)]

    edalizer.parse_args(MyFlow, backendargs)

    expected: object = None

    # Convert provided command line value to expected type for the Edalize
    if value is None and datatype != "bool":
        pass
    elif datatype == "bool":
        if value is None or str(value).lower() in ("yes", "true", "t", "y", "1"):
            expected = True
        else:
            expected = False
    elif datatype == "int":
        expected = int(value)
    elif datatype == "real":
        expected = float(value)
    elif datatype == "str":
        expected = str(value)
    elif datatype == "list":
        expected = shlex.split(str(value))
    elif datatype == "file":
        expected = str(Path(value).resolve())

    assert edalizer.edam["parameters"] == {}

    if expected is None and datatype != "bool":
        # Option was defined but not used
        assert edalizer.activated_flow_options == {}
        assert name not in edalizer.edam["flow_options"]
    else:
        # Option was defined and used
        assert edalizer.activated_flow_options == {name: expected}
        assert edalizer.edam["flow_options"][name] == expected


@pytest.mark.parametrize(
    "datatype,value,default",
    (
        ("bool", None, None),
        ("bool", "FalSE", True),
        ("bool", "f", True),
        ("bool", "No", True),
        ("bool", "n", True),
        ("bool", "0", True),
        ("bool", "tRuE", False),
        ("bool", "t", False),
        ("bool", "Yes", False),
        ("bool", "y", False),
        ("bool", "1", False),
        ("int", None, None),
        ("int", -2137, 10),
        ("int", 0, 2137),
        ("int", 2137, -10),
        ("real", None, None),
        ("real", -0.25, 5),
        ("real", 0.0, 5.0),
        ("real", 0.25, -5),
        ("str", None, None),
        ("str", "", "default"),
        ("str", "arg", "default"),
        ("str", "arg with spaces", "default"),
        ("file", None, None),
        ("file", "input.tcl", "default.tcl"),
    ),
)
@pytest.mark.parametrize(
    "paramtype",
    (
        "plusarg",
        "vlogparam",
        "vlogdefine",
        "generic",
        "cmdlinearg",
    ),
)
def test_edalizer_parse_args_for_parameters(
    datatype: str, value: object, default: object, paramtype: str
) -> None:
    """Test parsing arguments for parameters by the Edalizer class."""
    from edalize.flows.edaflow import Edaflow

    from fusesoc.edalizer import Edalizer

    name = f"my_{datatype}_parameter"

    class MyFlow(Edaflow):
        argtypes = [paramtype]

        FLOW_OPTIONS = {}

    edalizer = Edalizer(
        toplevel=None,
        flags=None,
        work_root=None,
        core_manager=None,
    )

    edalizer.edam = {
        "name": "flow",
        "flow_options": {},
        "parameters": {
            name: {
                "datatype": datatype,
                "paramtype": paramtype,
                "default": default,
            },
        },
    }

    backendargs: list[str]

    if value is None:
        backendargs = [f"--{name}"] if datatype == "bool" else []
    else:
        backendargs = [f"--{name}", str(value)]

    edalizer.parse_args(MyFlow, backendargs)

    expected: object = None

    # Convert provided command line value to expected type for the Edalize
    if value is None and datatype != "bool":
        pass
    elif datatype == "bool":
        if value is None or str(value).lower() in ("yes", "true", "t", "y", "1"):
            expected = True
        else:
            expected = False
    elif datatype == "int":
        expected = int(value)
    elif datatype == "real":
        expected = float(value)
    elif datatype == "str":
        expected = str(value)
    elif datatype == "file":
        expected = str(Path(value).resolve())

    assert edalizer.activated_flow_options == {}
    assert edalizer.edam["flow_options"] == {}
    assert edalizer.edam["parameters"][name]["default"] == expected
