# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import os.path
import tempfile

from test_common import cache_root, cores_root, library_root

from fusesoc.config import Config

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


import pytest


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
