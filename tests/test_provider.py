# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import shutil
import tempfile

import pytest
from test_common import tests_dir

from fusesoc.capi2.coreparser import Core2Parser
from fusesoc.core import Core

cores_root = os.path.join(tests_dir, "cores")


@pytest.mark.network
def test_git_provider():
    cache_root = tempfile.mkdtemp("git_")
    core = Core(
        Core2Parser(), os.path.join(cores_root, "misc", "gitcore.core"), cache_root
    )

    core.setup()

    for f in [
        "LICENSE",
        "README.md",
        "wb_common.core",
        "wb_common.v",
        "wb_common_params.v",
    ]:
        assert os.path.isfile(os.path.join(core.files_root, f))


@pytest.mark.network
def test_github_provider():
    cache_root = tempfile.mkdtemp("github_")
    core = Core(
        Core2Parser(),
        os.path.join(cores_root, "vlog_tb_utils", "vlog_tb_utils-1.1.core"),
        cache_root,
    )

    core.setup()

    for f in [
        "LICENSE",
        "vlog_functions.v",
        "vlog_tap_generator.v",
        "vlog_tb_utils.core",
        "vlog_tb_utils.v",
    ]:
        assert os.path.isfile(os.path.join(core.files_root, f))
        ref_dir = os.path.join(os.path.dirname(__file__), __name__)
        f = "vlog_functions.v"
    with (
        open(os.path.join(ref_dir, f)) as fref,
        open(os.path.join(core.files_root, f)) as fgen,
    ):
        assert fref.read() == fgen.read(), f


@pytest.mark.skipif(shutil.which("svn") is None, reason="Subversion not installed")
def test_svn_provider():
    cache_root = tempfile.mkdtemp("svn_")
    core = Core(
        Core2Parser(),
        os.path.join(cores_root, "misc", "svn.core"),
        cache_root,
    )

    core.setup()
    assert os.path.isfile(os.path.join(core.files_root, "gtkwave.desktop"))


@pytest.mark.skip(reason="Problems connecting to OpenCores SVN")
def test_opencores_provider():
    cache_root = tempfile.mkdtemp("opencores_")
    core = Core(
        Core2Parser(),
        os.path.join(cores_root, "misc", "opencorescore.core"),
        cache_root,
    )

    core.setup()

    assert os.path.isfile(os.path.join(core.files_root, "tap_defines.v"))
    assert os.path.isfile(os.path.join(core.files_root, "tap_top.v"))


@pytest.mark.network
def test_url_provider():
    cores_root = os.path.join(tests_dir, "capi2_cores", "providers")

    for corename in ["url_simple", "url_simple_with_user_agent", "url_tar", "url_zip"]:
        cache_root = tempfile.mkdtemp(prefix="url_")
        core = Core(
            Core2Parser(), os.path.join(cores_root, corename + ".core"), cache_root
        )
        core.setup()
        assert os.path.isfile(os.path.join(core.files_root, "file.v"))


def test_url_provider_user_agent(monkeypatch, tmp_path):
    from fusesoc.provider.url import Url

    cores_root = os.path.join(tests_dir, "capi2_cores", "providers")
    core = Core(
        Core2Parser(),
        os.path.join(cores_root, "url_simple_with_user_agent.core"),
        str(tmp_path),
    )
    calls = []
    monkeypatch.setattr(Url, "_download", lambda *args: calls.append(args))
    core.provider._checkout(str(tmp_path / "out"))
    assert calls[0][3] == "FuseSoC"


def test_uncachable():
    cores_root = os.path.join(tests_dir, "capi2_cores", "misc")
    cache_root = tempfile.mkdtemp("uncachable_")
    core = Core(Core2Parser(), os.path.join(cores_root, "uncachable.core"), cache_root)
    assert core.cache_status() == "outofdate"


@pytest.mark.skip(reason="Problems connecting to OpenCores SVN")
def test_cachable():
    cache_root = tempfile.mkdtemp("opencores_")
    core = Core(
        Core2Parser(),
        os.path.join(cores_root, "misc", "opencorescore.core"),
        cache_root,
    )
    assert core.cache_status() == "empty"
    core.setup()
    assert core.cache_status() == "downloaded"


# The hash of `tests/test_provider/file.tar.gz`.
FILE_TAR_SHA256 = "ad12e833bedfc2833e7e57315c1a68ba282ddcbe157c8f84ecb68dc3d69fc063"


def _url_core(tmp_path, sha256):
    """A `url` core downloading `file.tar.gz` over file://, with the given hash."""
    url = "file://" + os.path.join(tests_dir, "test_provider", "file.tar.gz")
    core_file = tmp_path / "url_sha.core"
    core_file.write_text(
        "CAPI=2:\nname: ::url_sha:0\n"
        f"provider: {{name: url, filetype: tar, url: '{url}', sha256: '{sha256}'}}\n"
    )
    return Core(Core2Parser(), str(core_file), str(tmp_path / "cache"))


def test_url_provider_sha256_matches(tmp_path):
    # The hash is case-insensitive.
    core = _url_core(tmp_path, FILE_TAR_SHA256.upper())
    core.setup()
    assert os.path.isfile(os.path.join(core.files_root, "file.v"))


def test_url_provider_sha256_mismatch(tmp_path):
    wrong = "0" * 64
    core = _url_core(tmp_path, wrong)
    with pytest.raises(RuntimeError) as excinfo:
        core.setup()
    msg = str(excinfo.value)
    assert "file.tar.gz" in msg and wrong in msg and FILE_TAR_SHA256 in msg
    # Nothing was unpacked.
    assert not os.path.exists(os.path.join(core.files_root, "file.v"))


def test_url_provider_sha256_must_be_hex(tmp_path):
    # The schema rejects the provider section; the message does not name sha256.
    with pytest.raises(SyntaxError, match="provider cannot be validated"):
        _url_core(tmp_path, "abc")
