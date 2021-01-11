# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest


def test_deptree(tmp_path):
    import os

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    tests_dir = os.path.dirname(__file__)
    deptree_cores_dir = os.path.join(tests_dir, "capi2_cores", "deptree")
    lib = Library("deptree", deptree_cores_dir)

    cm = CoreManager(Config())
    cm.add_library(lib)

    root_core = cm.get_core(Vlnv("::deptree-root"))

    # This is an array of (child, parent) core name tuples and
    # is used for checking that the flattened list of core
    # names is consistent with the dependencies.
    dependencies = (
        # Dependencies of the root core
        ("::deptree-child3:0", "::deptree-root:0"),
        ("::deptree-child2:0", "::deptree-root:0"),
        ("::deptree-child1:0", "::deptree-root:0"),
        ("::deptree-child-a:0", "::deptree-root:0"),
        # Dependencies of child1 core
        ("::deptree-child3:0", "::deptree-child1:0"),
        # Dependencies of child-a core
        ("::deptree-child4:0", "::deptree-child-a:0"),
    )

    # The ordered files that we expect from each core.
    expected_core_files = {
        "::deptree-child3:0": (
            "child3-fs1-f1.sv",
            "child3-fs1-f2.sv",
        ),
        "::deptree-child2:0": (
            "child2-fs1-f1.sv",
            "child2-fs1-f2.sv",
        ),
        "::deptree-child1:0": (
            "child1-fs1-f1.sv",
            "child1-fs1-f2.sv",
        ),
        "::deptree-child4:0": ("child4.sv",),
        "::deptree-child-a:0": (
            # Files from filesets are always included before any
            # files from generators with "position: append".
            # This is because generated files are often dependent on files
            # that are not generated, and it convenient to be able to
            # include them in the same core.
            "child-a2.sv",
            "generated-child-a.sv",
            "generated-child-a-append.sv",
        ),
        "::deptree-root:0": (
            "root-fs1-f1.sv",
            "root-fs1-f2.sv",
            "root-fs2-f1.sv",
            "root-fs2-f2.sv",
        ),
    }

    # Use Edalizer to get the files.
    # This is necessary because we need to run generators.
    work_root = str(tmp_path / "work")
    cache_root = str(tmp_path / "cache")
    os.mkdir(work_root)
    os.mkdir(cache_root)
    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        cache_root=cache_root,
        work_root=work_root,
        core_manager=cm,
    )
    edalizer.run()

    # Check dependency tree (after running all generators)
    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    all_core_names = set()
    for child, parent in dependencies:
        assert child in deps_names
        assert parent in deps_names
        all_core_names.add(child)
        all_core_names.add(parent)
    # Confirm that we don't have any extra or missing core names.
    assert all_core_names == set(deps_names)
    # Make sure there are no repeats in deps_names
    assert len(all_core_names) == len(deps_names)

    # Now work out what order we expect to get the filenames.
    # The order of filenames within each core in deterministic.
    # Each fileset in order. Followed by each generator in order.
    # The order between the cores is taken the above `dep_names`.
    expected_filenames = []
    # A generator-created core with "position: first"
    expected_filenames.append("generated-child-a-first.sv")
    for dep_name in deps_names:
        expected_filenames += list(expected_core_files[dep_name])
    # A generator-created core with "position: last"
    expected_filenames.append("generated-child-a-last.sv")

    edalized_filenames = [
        os.path.basename(f["name"]) for f in edalizer.edalize["files"]
    ]

    assert edalized_filenames == expected_filenames


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
        {
            "file_type": "user",
            "core": "::copytocore:0",
            "name": "copied.file",
        },
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
