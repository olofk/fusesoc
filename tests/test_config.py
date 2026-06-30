# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import os.path
import tempfile

import pytest
from test_common import cache_root, cores_root, library_root

from fusesoc.config import Config
from fusesoc.main import _effective_config_path

build_root = "test_build_root"

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
cores_root = {cores_root}
library_root = {library_root}

[library.test_lib]
location = {library_root}/test_lib
auto-sync = false
sync-uri = https://github.com/fusesoc/fusesoc-cores
"""


def test_config():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(
        EXAMPLE_CONFIG.format(
            build_root=build_root,
            cache_root=cache_root,
            cores_root=cores_root,
            library_root=library_root,
        )
    )
    tcf.seek(0)

    conf = Config(tcf.name)

    assert conf.library_root == library_root


@pytest.mark.parametrize("from_cli", [False, True])
@pytest.mark.parametrize("from_config", [False, True])
def test_config_filters(from_cli, from_config):
    import tempfile

    from fusesoc.config import Config

    if from_config:
        tcf = tempfile.NamedTemporaryFile(mode="w+")
        tcf.write("[main]\nfilters = configfilter1 configfilter2\n")
        tcf.seek(0)
        config = Config(tcf.name)
    else:
        config = Config()

    if from_cli:
        config.args_filters = ["clifilter1", "clifilter2"]

    expected = {
        (False, False): [],
        (False, True): ["configfilter1", "configfilter2"],
        (True, False): ["clifilter1", "clifilter2"],
        (True, True): ["configfilter1", "configfilter2", "clifilter1", "clifilter2"],
    }
    assert config.filters == expected[(from_cli, from_config)]


def test_config_relative_path():
    with tempfile.TemporaryDirectory() as td:
        config_path = os.path.join(td, "fusesoc.conf")
        with open(config_path, "w") as tcf:
            tcf.write(
                EXAMPLE_CONFIG.format(
                    build_root="build_root",
                    cache_root="cache_root",
                    cores_root="cores_root",
                    library_root="library_root",
                )
            )

        conf = Config(tcf.name)
        for name in ["build_root", "cache_root", "library_root"]:
            abs_td = os.path.realpath(td)
            assert getattr(conf, name) == os.path.join(abs_td, name)


def test_config_relative_path_starts_with_dot():
    with tempfile.TemporaryDirectory() as td:
        config_path = os.path.join(td, "fusesoc.conf")
        with open(config_path, "w") as tcf:
            tcf.write(
                EXAMPLE_CONFIG.format(
                    build_root="./build_root",
                    cache_root="./cache_root",
                    cores_root="./cores_root",
                    library_root="./library_root",
                )
            )

        conf = Config(tcf.name)
        for name in ["build_root", "cache_root", "library_root"]:
            abs_td = os.path.realpath(td)
            assert getattr(conf, name) == os.path.join(abs_td, name)


def test_config_relative_path_with_local_config():
    prev_dir = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        config_path = "fusesoc.conf"
        with open(config_path, "w") as tcf:
            tcf.write(
                EXAMPLE_CONFIG.format(
                    build_root="build_root",
                    cache_root="cache_root",
                    cores_root="cores_root",
                    library_root="library_root",
                )
            )

        conf = Config(tcf.name)
        for name in ["build_root", "cache_root", "library_root"]:
            abs_td = os.path.realpath(td)
            assert getattr(conf, name) == os.path.join(abs_td, name)
    os.chdir(prev_dir)


def test_config_libraries():
    tcf = tempfile.NamedTemporaryFile(mode="w+")
    tcf.write(
        EXAMPLE_CONFIG.format(
            build_root=build_root,
            cache_root=cache_root,
            cores_root=cores_root,
            library_root=library_root,
        )
    )
    tcf.seek(0)

    conf = Config(tcf.name)

    lib = None
    for library in conf.libraries:
        if library.name == "test_lib":
            lib = library
    assert lib

    assert lib.location == os.path.join(library_root, "test_lib")
    assert lib.sync_uri == "https://github.com/fusesoc/fusesoc-cores"
    assert not lib.auto_sync


def test_config_write():
    tcf = tempfile.NamedTemporaryFile(mode="w+", delete=False)
    tcf.write(
        EXAMPLE_CONFIG.format(
            build_root=build_root,
            cache_root=cache_root,
            cores_root=cores_root,
            library_root=library_root,
        )
    )
    tcf.flush()

    with Config(tcf.name) as c:
        c.build_root = "/tmp"

    conf = Config(tcf.name)

    assert conf.build_root == "/tmp"
    os.remove(tcf.name)


def test_effective_config_path_env_var(monkeypatch):
    monkeypatch.setenv("FUSESOC_CONFIG", "/some/path/fusesoc.conf")
    assert _effective_config_path(None) == "/some/path/fusesoc.conf"


def test_effective_config_path_cli_overrides_env_var(monkeypatch):
    monkeypatch.setenv("FUSESOC_CONFIG", "/env/path/fusesoc.conf")
    assert _effective_config_path("/cli/path/fusesoc.conf") == "/cli/path/fusesoc.conf"


def test_effective_config_path_no_env_var_no_cli(monkeypatch):
    monkeypatch.delenv("FUSESOC_CONFIG", raising=False)
    assert _effective_config_path(None) is None


def test_config_missing_file_logs_warning(tmp_path, caplog):
    import logging

    missing = str(tmp_path / "nonexistent.conf")
    with caplog.at_level(logging.WARNING, logger="fusesoc.config"):
        Config(missing, create_if_missing=False)
    assert any(missing in m for m in caplog.messages)


def test_config_missing_file_does_not_create_file(tmp_path, caplog):
    missing = tmp_path / "nonexistent.conf"
    Config(str(missing), create_if_missing=False)
    assert not missing.exists()


def test_config_missing_file_creates_file_when_allowed(tmp_path):
    new_conf = tmp_path / "new.conf"
    Config(str(new_conf), create_if_missing=True)
    assert new_conf.exists()


def test_config_missing_file_no_warning_when_create_allowed(tmp_path, caplog):
    import logging

    new_conf = tmp_path / "new.conf"
    with caplog.at_level(logging.WARNING, logger="fusesoc.config"):
        Config(str(new_conf), create_if_missing=True)
    assert not caplog.records


def test_config_loaded_via_env_var(monkeypatch):
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".conf", delete=False) as tcf:
        tcf.write(
            EXAMPLE_CONFIG.format(
                build_root=build_root,
                cache_root=cache_root,
                cores_root=cores_root,
                library_root=library_root,
            )
        )
        config_path = tcf.name

    try:
        monkeypatch.setenv("FUSESOC_CONFIG", config_path)
        conf = Config(_effective_config_path(None))
        assert conf.library_root == library_root
    finally:
        os.remove(config_path)
