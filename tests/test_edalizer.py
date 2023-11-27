# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause


def test_apply_filters(caplog):
    import logging

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

    with caplog.at_level(logging.WARNING):
        edalizer.apply_filters(["doesnotexist"])

    assert "Ignoring unknown EDAM filter 'doesnotexist'" in caplog.text
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
    import os
    import shutil
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    tests_dir = os.path.dirname(__file__)
    cores_dir = os.path.join(tests_dir, "capi2_cores", "misc", "generate")

    lib = Library("edalizer", cores_dir)

    cm = CoreManager(Config())
    cm.add_library(lib, [])

    core = cm.get_core(Vlnv("::generate"))

    build_root = tempfile.mkdtemp(prefix="export_")
    export_root = os.path.join(build_root, "exported_files")

    edalizer = Edalizer(
        toplevel=core.name,
        flags={"tool": "icarus"},
        core_manager=cm,
        work_root=os.path.join(build_root, "work"),
        export_root=export_root,
        system_name=None,
    )
    edalizer.run()

    ref_edam = {
        "version": "0.2.1",
        "name": "generate_0",
        "toplevel": "na",
        "dependencies": {
            "::generators:0": [],
            "::generate:0": [
                "::generators:0",
                "::generate-testgenerate_without_params:0",
                "::generate-testgenerate_with_params:0",
                "::generate-testgenerate_with_override:0",
                "::generate-testgenerate_with_cache:0",
            ],
            "::generate-testgenerate_without_params:0": [],
            "::generate-testgenerate_with_params:0": [],
            "::generate-testgenerate_with_override:0": [],
            "::generate-testgenerate_with_cache:0": [],
        },
        "parameters": {"p": {"datatype": "str", "paramtype": "vlogparam"}},
        "tool_options": {"icarus": {}},
        "flow_options": {},
        "hooks": {},
        "files": [],
        "filters": [],
        "vpi": [],
    }

    assert ref_edam == edalizer.edam
    edalizer.export()

    name_to_core = {str(core.name): core for core in edalizer.cores}
    for flavour in ["testgenerate_with_params", "testgenerate_without_params"]:
        core_name = f"::generate-{flavour}:0"
        assert core_name in name_to_core
        core = name_to_core[core_name]

        # ttptttg temporary directory should be removed by now
        assert not os.path.isdir(core.core_root)

    # Test generator input cache and file_input_params
    core_name = f"::generate-testgenerate_with_cache:0"
    assert core_name in name_to_core
    core = name_to_core[core_name]
    assert os.path.isdir(core.core_root)

    hash = ""
    with open(os.path.join(core.core_root, ".fusesoc_file_input_hash")) as f:
        hash = f.read()

    # SHA256 hash of test file content
    assert hash == "da265f9dccc9d9e64d059f677508f9550b403c99e6ce5df07c6fb1d711d0ee99"

    shutil.rmtree(core.core_root, ignore_errors=True)
