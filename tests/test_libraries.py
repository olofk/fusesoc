# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import shutil
import subprocess
import tempfile
from textwrap import dedent
from argparse import Namespace

from test_common import cache_root, cores_root, library_root

from fusesoc.config import Config
from fusesoc.fusesoc import Fusesoc

build_root = "test_build_root"

EXAMPLE_CONFIG = """
[main]
build_root = {build_root}
cache_root = {cache_root}
library_root = {library_root}

[library.test_lib]
location = {cores_root}
auto-sync = {auto_sync}
sync-uri = {sync_uri}
sync-type = {sync_type}
"""

sync_uri = "https://github.com/fusesoc/fusesoc-cores"


def test_library_location():

    with tempfile.NamedTemporaryFile(mode="w+") as tcf:
        tcf.write(
            EXAMPLE_CONFIG.format(
                build_root=build_root,
                cache_root=cache_root,
                cores_root=cores_root,
                library_root=library_root,
                auto_sync="false",
                sync_uri=sync_uri,
                sync_type="git",
            )
        )
        tcf.flush()

        conf = Config(tcf.name)

    fs = Fusesoc(conf)

    fs.get_core("mor1kx-generic")
    fs.get_core("atlys")


def test_library_add(caplog):
    import tempfile

    from fusesoc.coremanager import CoreManager
    from fusesoc.main import add_library

    with tempfile.TemporaryDirectory() as td:
        clone_target = os.path.join(td, "clone-target")
        library_root = os.path.join(td, "library-root")
        conf_path = os.path.join(td, "fusesoc.conf")

        conf = Config(conf_path)
        conf.library_root = library_root
        cm = CoreManager(conf)

        args = Namespace()
        args.name = "fusesoc-cores"
        args.location = clone_target
        args.config = conf_path
        args.no_auto_sync = False
        vars(args)["sync-uri"] = sync_uri

        add_library(cm, args)

        expected = """[library.fusesoc-cores]
location = {}
sync-uri = https://github.com/fusesoc/fusesoc-cores
sync-type = git
auto-sync = true""".format(
            os.path.abspath(clone_target)
        )

        with open(conf_path) as tcf:
            result = tcf.read().strip()

    assert expected == result

    with tempfile.NamedTemporaryFile(mode="w+") as tcf:
        args.config = tcf.name
        args.location = None
        vars(args)["sync-type"] = "git"

        expected = """[library.fusesoc-cores]
location = fusesoc_libraries/fusesoc-cores
sync-uri = https://github.com/fusesoc/fusesoc-cores
sync-type = git
auto-sync = true"""

        add_library(cm, args)

        tcf.seek(0)
        result = tcf.read().strip()

    assert expected == result
    shutil.rmtree("fusesoc_libraries")

    with tempfile.NamedTemporaryFile() as tcf:
        args.config = tcf.name
        vars(args)["sync-type"] = "local"
        vars(args)["sync-uri"] = "tests/capi2_cores"
        args.location = None

        with caplog.at_level(logging.INFO):
            add_library(cm, args)

    assert (
        "Interpreting sync-uri 'tests/capi2_cores' as location for local provider."
        in caplog.text
    )

    tcf = tempfile.NamedTemporaryFile(mode="w+")
    args.config = tcf.name

    vars(args)["sync-type"] = "git"
    vars(args)["sync-uri"] = sync_uri
    vars(args)["sync-version"] = "capi2"
    args.location = None

    expected = dedent("""
        [library.fusesoc-cores]
        location = fusesoc_libraries/fusesoc-cores
        sync-uri = https://github.com/fusesoc/fusesoc-cores
        sync-version = capi2
        sync-type = git
        auto-sync = true
    """)

    add_library(cm, args)

    tcf.seek(0)
    result = tcf.read().strip()

    assert expected == result
    shutil.rmtree("fusesoc_libraries")
    tcf.close()


def test_library_update(caplog):

    clone_target = tempfile.mkdtemp()

    subprocess.call(["git", "clone", sync_uri, clone_target])

    with tempfile.NamedTemporaryFile(mode="w+") as tcf:
        tcf.write(
            EXAMPLE_CONFIG.format(
                build_root=build_root,
                cache_root=cache_root,
                cores_root=clone_target,
                library_root=library_root,
                auto_sync="false",
                sync_uri=sync_uri,
                sync_type="git",
            )
        )
        tcf.flush()

        conf = Config(tcf.name)

    Fusesoc.init_logging(False, False)
    fs = Fusesoc(conf)

    with caplog.at_level(logging.INFO):
        fs.update_libraries([])

    assert "test_lib : auto-sync disabled. Ignoring update" in caplog.text

    caplog.clear()

    with caplog.at_level(logging.INFO):
        fs.update_libraries(["test_lib"])

    assert "test_lib : Updating..." in caplog.text

    caplog.clear()

    _library = fs.get_library("test_lib")
    _library.auto_sync = True

    with caplog.at_level(logging.INFO):
        fs.update_libraries([])

    assert "test_lib : Updating..." in caplog.text

    caplog.clear()

    tcf.close()

    _library.sync_type = "local"

    with caplog.at_level(logging.INFO):
        fs.update_libraries([])

    assert "test_lib : sync-type is local. Ignoring update" in caplog.text


def test_library_update_with_initialize(caplog):
    with tempfile.TemporaryDirectory() as library:

        with tempfile.NamedTemporaryFile(mode="w+") as tcf:
            tcf.write(
                f"""[main]
library_root = {library}

[library.vlog_tb_utils]
location = {library}/vlog_tb_utils
sync-uri = https://github.com/fusesoc/vlog_tb_utils
sync-type = git
auto-sync = true

"""
            )
            tcf.flush()

            conf = Config(tcf.name)

        Fusesoc.init_logging(False, False)
        fs = Fusesoc(conf)

        with caplog.at_level(logging.INFO):
            fs.update_libraries([])

        assert "vlog_tb_utils does not exist. Trying a checkout" in caplog.text
        assert f"Cloning library into {library}/vlog_tb_utils" in caplog.text
        assert "Updating..." in caplog.text
