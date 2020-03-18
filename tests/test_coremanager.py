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
        files += [f.name for f in d.get_files({})]

    assert files == files_expected


def test_copyto():
    import os
    import tempfile

    from fusesoc.edalizer import Edalizer
    from fusesoc.core import Core

    core = Core(
        os.path.join(os.path.dirname(__file__), "cores", "misc", "copytocore.core")
    )
    flags = {"tool": "icarus"}

    work_root = tempfile.mkdtemp(prefix="copyto_")

    eda_api = Edalizer(core.name, flags, [core], None, work_root, None).edalize

    assert eda_api["files"] == [
        {
            "file_type": "user",
            "core": "::copytocore:0",
            "logical_name": "",
            "name": "copied.file",
            "is_include_file": False,
        },
        {
            "file_type": "tclSource",
            "core": "::copytocore:0",
            "logical_name": "",
            "name": "subdir/another.file",
            "is_include_file": False,
        },
    ]
    assert os.path.exists(os.path.join(work_root, "copied.file"))
    assert os.path.exists(os.path.join(work_root, "subdir", "another.file"))


def test_export():
    import os
    import tempfile

    from fusesoc.edalizer import Edalizer
    from fusesoc.core import Core

    core = Core(
        os.path.join(
            os.path.dirname(__file__), "cores", "wb_intercon", "wb_intercon-1.0.core"
        )
    )

    build_root = tempfile.mkdtemp(prefix="export_")
    export_root = os.path.join(build_root, "exported_files")
    eda_api = Edalizer(
        core.name,
        {"tool": "icarus"},
        [core],
        cache_root=None,
        work_root=os.path.join(build_root, "work"),
        export_root=export_root,
    ).edalize

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
