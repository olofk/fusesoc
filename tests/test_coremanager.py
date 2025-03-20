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
    cm.add_library(lib, [])

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
            # However, for peculiar cases when non-generated files actually depend on generated, "position: prepend" is also available
            "child-a2.sv",
            "generated-child-a-prepend.sv",
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
    os.mkdir(work_root)
    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        work_root=work_root,
        core_manager=cm,
    )
    edam = edalizer.run()

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

    edalized_filenames = [os.path.basename(f["name"]) for f in edam["files"]]

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
    cm.add_library(lib, [])

    core = cm.get_core(Vlnv("::copytocore"))

    edalizer = Edalizer(
        toplevel=core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
        export_root=None,
        system_name=None,
    )
    edam = edalizer.run()
    edalizer.export()

    assert edam["files"] == [
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
    cm.add_library(Library("cores", core_dir), [])

    core = cm.get_core(Vlnv("::wb_intercon"))

    edalizer = Edalizer(
        toplevel=core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
        export_root=export_root,
        system_name=None,
    )
    edalizer.run()
    edalizer.export()

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


def test_override(caplog):
    import logging
    import os

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    core_base_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "override")
    cm = CoreManager(Config())
    with caplog.at_level(logging.WARNING):
        cm.add_library(Library("1", os.path.join(core_base_dir, "1")), [])
    assert caplog.text == ""

    with caplog.at_level(logging.WARNING):
        cm.add_library(Library("2", os.path.join(core_base_dir, "2")), [])
    assert "Replacing ::basic:0 in" in caplog.text

    core = cm.get_core(Vlnv("::basic"))
    assert core.core_root.endswith("2")


def test_virtual():
    import os
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "virtual")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])

    test_vectors = {
        "::top_impl1": ["::impl1:0", "::user:0", "::top_impl1:0"],
        "::top_impl2": ["::impl2:0", "::user:0", "::top_impl2:0"],
    }
    for top_vlnv, expected_deps in test_vectors.items():
        root_core = cm.get_core(Vlnv(top_vlnv))

        edalizer = Edalizer(
            toplevel=root_core.name,
            flags=flags,
            core_manager=cm,
            work_root=work_root,
        )
        edalizer.run()

        deps = cm.get_depends(root_core.name, {})
        deps_names = [str(c) for c in deps]

        assert deps_names == expected_deps


def test_virtual_conflict():
    """
    Test virtual core selection when there are more than one selected implementation.
    This shall result in a conflict of cores.
    """
    import os
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager, DependencyError
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "virtual")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])

    root_core = cm.get_core(Vlnv("::top_conflict"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )
    with pytest.raises(DependencyError) as _:
        edalizer.run()


def test_virtual_non_deterministic_virtual(caplog):
    """
    Test virtual core selection when there are no selected implementations.
    This shall result in a warning that the virtual core selection is non-deteministic.
    """
    import logging
    import os
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "virtual")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])

    root_core = cm.get_core(Vlnv("::top_non_deterministic"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )
    edalizer.run()

    with caplog.at_level(logging.WARNING):
        edalizer.run()
    assert "Non-deterministic selection of virtual core" in caplog.text

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::impl1:0",
            "::impl2:0",
            "::user:0",
            "::top_non_deterministic:0",
        ]


def test_mapping_success_cases():
    from pathlib import Path

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    core_dir = Path(__file__).parent / "capi2_cores" / "mapping"

    top = "test_mapping:t:top"
    top_vlnv = Vlnv(top)

    for mappings, expected_deps in (
        (
            [],
            {
                "test_mapping:t:top:0",
                "test_mapping:l:a:0",
                "test_mapping:l:b:0",
                "test_mapping:l:c:0",
            },
        ),
        (
            [top],
            {
                "test_mapping:t:top:0",
                "test_mapping:l:f:0",
                "test_mapping:l:b:0",
                "test_mapping:l:c:0",
            },
        ),
        (
            ["test_mapping:l:d"],
            {
                "test_mapping:t:top:0",
                "test_mapping:l:a:0",
                "test_mapping:l:d:0",
                "test_mapping:l:e:0",
            },
        ),
        (
            [top, "test_mapping:l:d"],
            {
                "test_mapping:t:top:0",
                "test_mapping:l:f:0",
                "test_mapping:l:d:0",
                "test_mapping:l:e:0",
            },
        ),
        (
            ["test_mapping:l:c"],
            {
                "test_mapping:t:top:0",
                "test_mapping:l:a:0",
                "test_mapping:l:b:0",
            },
        ),
    ):
        cm = CoreManager(Config())
        cm.add_library(Library("mapping_test", core_dir), [])

        cm.db.mapping_set(mappings)

        actual_deps = {str(c) for c in cm.get_depends(top_vlnv, {})}

        assert expected_deps == actual_deps


def test_mapping_failure_cases():
    from pathlib import Path

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.librarymanager import Library

    core_dir = Path(__file__).parent / "capi2_cores" / "mapping"

    for mappings in (
        ["test_mapping:m:non_existent"],
        ["test_mapping:m:map_vers"],
        ["test_mapping:m:map_rec"],
        ["test_mapping:t:top", "test_mapping:l:c"],
        ["test_mapping:t:top", "test_mapping:t:top"],
    ):
        cm = CoreManager(Config())
        cm.add_library(Library("mapping_test", core_dir), [])

        with pytest.raises(RuntimeError):
            cm.db.mapping_set(mappings)


def test_lockfile(caplog):
    """
    Test core selection with a core pinned by a lock file
    """
    import logging
    import os
    import pathlib
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "dependencies")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])
    cm.db.load_lockfile(
        pathlib.Path(__file__).parent / "lockfiles" / "dependencies.lock.yml", True
    )

    root_core = cm.get_core(Vlnv("::dependencies-top"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )

    with caplog.at_level(logging.WARNING):
        edalizer.run()

    assert caplog.records == []

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::used:1.1",
            "::dependencies-top:0",
        ]


def test_lockfile_partial_warning(caplog):
    """
    Test core selection with a core pinned by a lock file
    """
    import logging
    import os
    import pathlib
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "dependencies")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])
    cm.db.load_lockfile(
        pathlib.Path(__file__).parent / "lockfiles" / "dependencies-partial.lock.yml",
        True,
    )

    root_core = cm.get_core(Vlnv("::dependencies-top"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )

    with caplog.at_level(logging.WARNING):
        edalizer.run()

    assert "Using lock file with partial list of cores" in caplog.text

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::used:1.1",
            "::dependencies-top:0",
        ]


def test_lockfile_version_warning(caplog):
    """
    Test core selection with a core pinned by a lock file, warning if version is out of scope
    """
    import logging
    import os
    import pathlib
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "dependencies")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])
    cm.db.load_lockfile(
        pathlib.Path(__file__).parent
        / "lockfiles"
        / "dependencies-partial-1.0.lock.yml",
        True,
    )

    root_core = cm.get_core(Vlnv("::dependencies-top"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )

    with caplog.at_level(logging.WARNING):
        edalizer.run()

    assert "Failed to pin" in caplog.text

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::used:1.1",
            "::dependencies-top:0",
        ]


def test_lockfile_no_file(caplog):
    """
    Test core selection with a core pinned by a lock file
    """
    import logging
    import os
    import pathlib
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "dependencies")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])
    filepath = pathlib.Path(__file__).parent / "lockfiles" / "missing.lock.yml"
    cm.db.load_lockfile(filepath, True)

    root_core = cm.get_core(Vlnv("::dependencies-top"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )

    with caplog.at_level(logging.WARNING):
        edalizer.run()

    assert f"Lockfile {filepath} not found" in caplog.text
    assert not filepath.exists()

    if filepath.exists():
        filepath.unlink()

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::used:1.1",
            "::dependencies-top:0",
        ]


def test_lockfile_no_file_create(caplog):
    """
    Test core selection with a core pinned by a lock file
    """
    import logging
    import os
    import pathlib
    import tempfile

    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.edalizer import Edalizer
    from fusesoc.librarymanager import Library
    from fusesoc.vlnv import Vlnv

    flags = {"tool": "icarus"}

    build_root = tempfile.mkdtemp(prefix="export_")
    work_root = os.path.join(build_root, "work")

    core_dir = os.path.join(os.path.dirname(__file__), "capi2_cores", "dependencies")

    cm = CoreManager(Config())
    cm.add_library(Library("virtual", core_dir), [])
    filepath = pathlib.Path(__file__).parent / "lockfiles" / "created.lock.yml"
    cm.db.load_lockfile(filepath, False)

    root_core = cm.get_core(Vlnv("::dependencies-top"))

    edalizer = Edalizer(
        toplevel=root_core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
    )

    with caplog.at_level(logging.WARNING):
        edalizer.run()

    assert f"Lockfile {filepath} not found" in caplog.text
    assert filepath.exists()

    if filepath.exists():
        filepath.unlink()

    deps = cm.get_depends(root_core.name, {})
    deps_names = [str(c) for c in deps]

    for dependency in deps_names:
        assert dependency in [
            "::used:1.1",
            "::dependencies-top:0",
        ]
