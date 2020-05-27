# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause


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
    cm.add_library(lib)

    core = cm.get_core(Vlnv("::generate"))

    build_root = tempfile.mkdtemp(prefix="export_")
    cache_root = tempfile.mkdtemp(prefix="export_cache_")
    export_root = os.path.join(build_root, "exported_files")

    edalizer = Edalizer(
        toplevel=core.name,
        flags={"tool": "icarus"},
        core_manager=cm,
        cache_root=cache_root,
        work_root=os.path.join(build_root, "work"),
        export_root=export_root,
        system_name=None,
    )
    edalizer.run()

    gendir = os.path.join(
        cache_root, "generated", "generate-testgenerate_without_params_0"
    )
    assert os.path.isfile(os.path.join(gendir, "generated.core"))
    assert os.path.isfile(os.path.join(gendir, "testgenerate_without_params_input.yml"))
    gendir = os.path.join(
        cache_root, "generated", "generate-testgenerate_with_params_0"
    )
    assert os.path.isfile(os.path.join(gendir, "generated.core"))
    assert os.path.isfile(os.path.join(gendir, "testgenerate_with_params_input.yml"))
