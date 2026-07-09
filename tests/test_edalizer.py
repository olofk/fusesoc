# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause


def test_apply_filters(caplog):
    import pytest

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
    import os
    import shutil
    import tempfile
    from pathlib import Path

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
        == "generate-testgenerate_with_cache_0-dd0cbabeb8396cc34c551cb738a9d4cbf1fb6ba0fafca24be5aa55c03839a40f"
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
        == "generate-testgenerate_with_file_cache_0-71f6f955798bff1e5f67c76f40f9715d5fc12e6ccbb8919fc607f9c222db7452"
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


def test_changing_generator_command_invalidates_cache_hash(tmp_path):
    """Changing the generator's ``command`` produces a different cache hash,
    so an updated generator does not reuse a previous run's cached output.

    Regression test for https://github.com/olofk/fusesoc/issues/751.
    """
    from types import SimpleNamespace

    from fusesoc.edalizer import Ttptttg
    from fusesoc.vlnv import Vlnv

    # Minimal core stand-in: Ttptttg only touches .name, .cache_root,
    # .files_root.
    fake_core = SimpleNamespace(
        name=Vlnv("::fake:0.1.0"),
        cache_root=str(tmp_path / "cache"),
        files_root=str(tmp_path / "src"),
    )

    ttptttg = {
        "generator": "mygen",
        "name": "inst",
        "pos": "append",
        "config": {"foo": "bar"},
    }

    def hash_with_cmd(cmd):
        generators = {
            "mygen": {
                "command": cmd,
                "interpreter": "python3",
                "root": str(tmp_path),
                "cache_type": "input",
            }
        }
        t = Ttptttg(ttptttg, fake_core, generators, str(tmp_path / "work"))
        return t._sha256_input_yaml_hexdigest()

    h_old = hash_with_cmd("gen_v1.py")
    h_new = hash_with_cmd("gen_v2.py")
    h_repeat = hash_with_cmd("gen_v1.py")

    assert h_old != h_new, "changing generator command changes the cache hash"
    assert h_old == h_repeat, "same command produces a stable hash"


def test_changing_generator_interpreter_invalidates_cache_hash(tmp_path):
    """Swapping the interpreter (e.g. ``python3`` → ``python2``)
    invalidates the cache."""
    from types import SimpleNamespace

    from fusesoc.edalizer import Ttptttg
    from fusesoc.vlnv import Vlnv

    fake_core = SimpleNamespace(
        name=Vlnv("::fake:0.1.0"),
        cache_root=str(tmp_path / "cache"),
        files_root=str(tmp_path / "src"),
    )
    ttptttg = {
        "generator": "mygen",
        "name": "inst",
        "pos": "append",
        "config": {},
    }

    def hash_with_interp(interp):
        generators = {
            "mygen": {
                "command": "gen.py",
                "interpreter": interp,
                "root": str(tmp_path),
                "cache_type": "input",
            }
        }
        t = Ttptttg(ttptttg, fake_core, generators, str(tmp_path / "work"))
        return t._sha256_input_yaml_hexdigest()

    assert hash_with_interp("python3") != hash_with_interp("python2")


def test_editing_generator_script_invalidates_cache_hash(tmp_path):
    """Editing the generator script in place -- same path, same
    declarations -- changes the cache hash, because the hash folds in a
    SHA-256 of the resolved script bytes.
    """
    from types import SimpleNamespace

    from fusesoc.edalizer import Ttptttg
    from fusesoc.vlnv import Vlnv

    gen_root = tmp_path / "gen"
    gen_root.mkdir()
    script = gen_root / "gen.py"

    fake_core = SimpleNamespace(
        name=Vlnv("::fake:0.1.0"),
        cache_root=str(tmp_path / "cache"),
        files_root=str(tmp_path / "src"),
    )
    ttptttg = {
        "generator": "mygen",
        "name": "inst",
        "pos": "append",
        "config": {},
    }
    generators = {
        "mygen": {
            "command": "gen.py",
            "interpreter": "python3",
            "root": str(gen_root),
            "cache_type": "input",
        }
    }

    def current_hash():
        t = Ttptttg(ttptttg, fake_core, generators, str(tmp_path / "work"))
        return t._sha256_input_yaml_hexdigest()

    # 1. Script missing -- hash is well-defined (None sentinel).
    h_missing = current_hash()

    # 2. Script created with v1 bytes -- hash flips.
    script.write_text("# generator v1\nprint('hello v1')\n")
    h_v1 = current_hash()
    assert h_v1 != h_missing

    # 3. Script edited in place to v2 -- hash flips again.
    script.write_text("# generator v2\nprint('hello v2')\n")
    h_v2 = current_hash()
    assert h_v2 != h_v1

    # 4. Reverting to v1 bytes -- hash returns to the v1 value
    # (proves the hash depends on bytes, not on "has the file been
    # touched"-style ctime/mtime heuristics).
    script.write_text("# generator v1\nprint('hello v1')\n")
    assert current_hash() == h_v1
