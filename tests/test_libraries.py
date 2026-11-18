# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import re
import shutil
import subprocess
import tempfile
from argparse import Namespace

import pytest
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


@pytest.mark.network
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
        args.sync_submodules = False
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

    expected = """[library.fusesoc-cores]
location = fusesoc_libraries/fusesoc-cores
sync-uri = https://github.com/fusesoc/fusesoc-cores
sync-version = capi2
sync-type = git
auto-sync = true"""

    add_library(cm, args)

    tcf.seek(0)
    result = tcf.read().strip()

    assert expected == result
    shutil.rmtree("fusesoc_libraries")
    tcf.close()


@pytest.mark.network
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


@pytest.mark.network
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

        assert (
            "vlog_tb_utils does not exist. Trying to initialize library" in caplog.text
        )
        assert f"Cloning library into {library}/vlog_tb_utils" in caplog.text
        assert "Updating..." in caplog.text


def _git_repo(path):
    """Create a git repo with one empty commit and return its file:// URI."""
    git = [
        "git",
        "-c",
        "user.name=test",
        "-c",
        "user.email=test@example.com",
        "-c",
        "commit.gpgsign=false",
    ]
    subprocess.run(git + ["init", "-q", str(path)], check=True)
    subprocess.run(
        git + ["-C", str(path), "commit", "-q", "--allow-empty", "-m", "init"],
        check=True,
    )
    return path.as_uri()


def test_library_add_existing_git_checkout(tmp_path, caplog):
    from fusesoc.library import Library

    uri = _git_repo(tmp_path / "repo")
    location = str(tmp_path / "fusesoc_libraries" / "mylib")
    subprocess.run(["git", "clone", "-q", uri, location], check=True)

    # Checkout of the same repo, e.g. after fusesoc.conf was lost: reuse it.
    # A .git suffix and trailing / do not count as a different origin.
    conf_path = str(tmp_path / "fusesoc.conf")
    with caplog.at_level(logging.INFO):
        Config(conf_path).add_library(Library("mylib", location, "git", uri + ".git/"))
    assert Config(conf_path).libraries[0].location == location
    assert f"Reusing existing checkout in {location}" in caplog.text
    assert not [r for r in caplog.records if r.levelname == "WARNING"]

    # Checkout of another repo: fail without writing the config
    other_uri = _git_repo(tmp_path / "other")
    other_conf = tmp_path / "other.conf"
    with pytest.raises(RuntimeError, match=f"has origin '{re.escape(uri)}'"):
        Config(str(other_conf)).add_library(
            Library("mylib", location, "git", other_uri)
        )
    assert not Config(str(other_conf)).libraries

    # Checkout without an origin remote: fail
    subprocess.run(["git", "-C", location, "remote", "remove", "origin"], check=True)
    with pytest.raises(RuntimeError, match="Cannot get origin"):
        Config(str(other_conf)).add_library(Library("mylib", location, "git", uri))
    subprocess.run(["git", "-C", location, "remote", "add", "origin", uri], check=True)

    # sync-version and sync-submodules are not applied to a reused checkout:
    # warn that a library update is needed
    for i, (version, submodules) in enumerate((("v1.0", False), (None, True))):
        caplog.clear()
        Config(str(tmp_path / f"sync{i}.conf")).add_library(
            Library("mylib", location, "git", uri, version, sync_submodules=submodules)
        )
        assert "Run 'fusesoc library update mylib'" in caplog.text

    # An insteadOf rewrite of the origin does not count as a different origin
    subprocess.run(
        ["git", "-C", location, "config", "url.https://example.com/.insteadOf", uri],
        check=True,
    )
    Config(str(tmp_path / "insteadof.conf")).add_library(
        Library("mylib", location, "git", uri)
    )

    # A relative local origin is resolved against the checkout
    subprocess.run(
        [
            "git",
            "-C",
            location,
            "remote",
            "set-url",
            "origin",
            os.path.relpath(tmp_path / "repo", location),
        ],
        check=True,
    )
    Config(str(tmp_path / "relative.conf")).add_library(
        Library("mylib", location, "git", str(tmp_path / "repo"))
    )


def test_library_add_existing_git_worktree(tmp_path, caplog):
    from fusesoc.library import Library

    # A worktree has a .git file instead of a .git directory
    uri = _git_repo(tmp_path / "repo")
    clone = str(tmp_path / "clone")
    location = str(tmp_path / "mylib")
    subprocess.run(["git", "clone", "-q", uri, clone], check=True)
    subprocess.run(
        ["git", "-C", clone, "worktree", "add", "-q", "--detach", location],
        check=True,
    )
    with caplog.at_level(logging.INFO):
        Config(str(tmp_path / "fusesoc.conf")).add_library(
            Library("mylib", location, "git", uri)
        )
    assert f"Reusing existing checkout in {location}" in caplog.text
    assert not [r for r in caplog.records if r.levelname == "WARNING"]


def test_library_add_existing_git_checkout_local_path(tmp_path, monkeypatch, caplog):
    from fusesoc.library import Library

    # git clone stores a relative local path as an absolute one, e.g.
    # /abs/./repo for ./repo. The same relative path must still match.
    monkeypatch.chdir(tmp_path)
    _git_repo(tmp_path / "repo")
    location = str(tmp_path / "mylib")
    subprocess.run(["git", "clone", "-q", "./repo", location], check=True)
    with caplog.at_level(logging.INFO):
        Config(str(tmp_path / "fusesoc.conf")).add_library(
            Library("mylib", location, "git", "./repo")
        )
    assert f"Reusing existing checkout in {location}" in caplog.text
