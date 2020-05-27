# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest


def test_deptree():
    from fusesoc.coremanager import CoreManager
    from fusesoc.config import Config
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv
    import os

    tests_dir = os.path.dirname(__file__)
    deptree_cores_dir = os.path.join(tests_dir, "capi2_cores", "deptree")
    lib = Library("deptree", deptree_cores_dir)

    cm = CoreManager(Config())
    cm.add_library(lib)

    root_core = cm.get_core(Vlnv("::deptree-root"))

    # Check dependency tree
    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]
    deps_names_expected = [
        "::deptree-child2:0",
        "::deptree-child3:0",
        "::deptree-child1:0",
        "::deptree-root:0",
    ]
    assert deps_names == deps_names_expected

    # Check files in dependency tree
    files_expected = [
        "child2-fs1-f1.sv",
        "child2-fs1-f2.sv",
        "child3-fs1-f1.sv",
        "child3-fs1-f2.sv",
        "child1-fs1-f1.sv",
        "child1-fs1-f2.sv",
        "root-fs1-f1.sv",
        "root-fs1-f2.sv",
        "root-fs2-f1.sv",
        "root-fs2-f2.sv",
    ]
    files = []
    for d in deps:
        files += [f["name"] for f in d.get_files({})]

    assert files == files_expected


def test_copyto():
    import os
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    work_root = tempfile.mkdtemp(prefix="copyto_")

    core_dir = os.path.join(os.path.dirname(__file__), "cores", "misc", "copytocore")
    lib = Library("misc", core_dir)

    cm = CoreManager(Config())
    cm.add_library(lib)

    core = cm.get_core(Vlnv("::copytocore"))

    edalizer = Edalizer(
        toplevel=core.name,
        flags=flags,
        core_manager=cm,
        cache_root=None,
        work_root=work_root,
        export_root=None,
        system_name=None,
    )
    edalizer.run()

    eda_api = edalizer.edalize

    assert eda_api["files"] == [
        {"file_type": "user", "core": "::copytocore:0", "name": "copied.file",},
        {
            "file_type": "tclSource",
            "core": "::copytocore:0",
            "name": "subdir/another.file",
        },
    ]
    assert os.path.exists(os.path.join(work_root, "copied.file"))
    assert os.path.exists(os.path.join(work_root, "subdir", "another.file"))


def test_export():
    import os
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    export_root = os.path.join(build_root, "exported_files")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "cores")

    cm = CoreManager(Config())
    cm.add_library(Library("cores", core_dir))

    core = cm.get_core(Vlnv("::wb_intercon"))

    edalizer = Edalizer(
        toplevel=core.name,
        flags=flags,
        core_manager=cm,
        cache_root=None,
        work_root=work_root,
        export_root=export_root,
        system_name=None,
    )
    edalizer.run()

    for f in [
        "wb_intercon_1.0/dummy_icarus.v",
        "wb_intercon_1.0/bench/wb_mux_tb.v",
        "wb_intercon_1.0/bench/wb_upsizer_tb.v",
        "wb_intercon_1.0/bench/wb_intercon_tb.v",
        "wb_intercon_1.0/bench/wb_arbiter_tb.v",
        "wb_intercon_1.0/rtl/verilog/wb_data_resize.v",
        "wb_intercon_1.0/rtl/verilog/wb_mux.v",
        "wb_intercon_1.0/rtl/verilog/wb_arbiter.v",
        "wb_intercon_1.0/rtl/verilog/wb_upsizer.v",
    ]:
        assert os.path.isfile(os.path.join(export_root, f))
