# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import subprocess
from pathlib import Path

import pytest

from fusesoc.library import Library
from fusesoc.provider.git import Git


def git(directory: Path, *args: str) -> str:
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(directory),
            "-c",
            "user.name=FuseSoC test",
            "-c",
            "user.email=test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        text=True,
    ).strip()


def commit(directory: Path, content: str) -> str:
    (directory / "design.v").write_text(content)
    git(directory, "add", "design.v")
    git(directory, "commit", "-qm", content)
    return git(directory, "rev-parse", "HEAD")


@pytest.fixture
def repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    source = tmp_path / "remote"
    source.mkdir()
    git(source, "init", "-q", "-b", "main")
    initial = commit(source, "initial")
    git(source, "tag", "v1")
    return source, initial


@pytest.mark.parametrize("version", ["main", "v1", "full-sha", "short-sha", None])
def test_git_library_updates_only_branches(repository, tmp_path: Path, version):
    source, initial = repository
    if version == "full-sha":
        version = initial
    elif version == "short-sha":
        version = initial[:10]
    location = tmp_path / "library"
    library = Library("test", str(location), "git", str(source), version)
    Git.init_library(library)
    latest = commit(source, "updated")

    Git.update_library(library)

    expected = latest if version in ("main", None) else initial
    assert git(location, "rev-parse", "HEAD") == expected
    assert (location / "design.v").read_text() == (
        "updated" if expected == latest else "initial"
    )


def test_git_library_can_select_new_remote_branch(repository, tmp_path: Path):
    source, _ = repository
    location = tmp_path / "library"
    library = Library("test", str(location), "git", str(source), "main")
    Git.init_library(library)
    git(source, "switch", "-c", "new-release")
    latest = commit(source, "new release")
    library.sync_version = "new-release"

    Git.update_library(library)

    assert git(location, "rev-parse", "HEAD") == latest


def test_git_library_refuses_divergent_history(repository, tmp_path: Path):
    source, _ = repository
    location = tmp_path / "library"
    library = Library("test", str(location), "git", str(source), "main")
    Git.init_library(library)
    local = commit(location, "local commit")
    commit(source, "remote commit")

    with pytest.raises(RuntimeError):
        Git.update_library(library)

    assert git(location, "rev-parse", "HEAD") == local
    assert (location / "design.v").read_text() == "local commit"


def test_git_library_preserves_conflicting_local_edits(repository, tmp_path: Path):
    source, initial = repository
    location = tmp_path / "library"
    library = Library("test", str(location), "git", str(source), "main")
    Git.init_library(library)
    (location / "design.v").write_text("uncommitted work")
    commit(source, "remote update")

    with pytest.raises(RuntimeError):
        Git.update_library(library)

    assert git(location, "rev-parse", "HEAD") == initial
    assert (location / "design.v").read_text() == "uncommitted work"
