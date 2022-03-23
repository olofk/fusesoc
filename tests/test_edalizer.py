# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause


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
        "hooks": {},
        "name": "flow_0",
        "parameters": {},
        "tool_options": {},
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

    name_to_core = {str(core.name): core for core in edalizer.cores}
    for flavour in ["testgenerate_with_params", "testgenerate_without_params"]:
        core_name = f"::generate-{flavour}:0"
        assert core_name in name_to_core
        core = name_to_core[core_name]

        # ttptttg temporary directory should be removed by now
        assert not os.path.isdir(core.core_root)
