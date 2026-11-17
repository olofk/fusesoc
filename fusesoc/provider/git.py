# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import subprocess

from fusesoc.library import Library
from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)


def _normalize_uri(uri: str) -> str:
    """Resolve local paths, which git clone stores as absolute paths, and strip
    a trailing / and .git suffix, which do not change the repository."""
    if os.path.isdir(uri):
        return os.path.realpath(uri)
    return uri.rstrip("/").removesuffix(".git")


class Git(Provider):
    @staticmethod
    def _checkout_library_version(library: Library) -> None:
        git_args = ["-C", library.location, "checkout", "-q", library.sync_version]

        if library.sync_version:
            logger.info(
                "Checked out {} at version {}".format(
                    library.name, library.sync_version
                )
            )
            Launcher("git", git_args).run()

    @staticmethod
    def _update_library_submodules(library: Library) -> None:
        if library.sync_submodules:
            logger.info(f"Updating submodules for {library.name}")
            git_args = [
                "-C",
                library.location,
                "submodule",
                "update",
                "--init",
                "--recursive",
            ]
            Launcher("git", git_args).run()

    @staticmethod
    def init_library(library: Library) -> None:
        # Reuse an existing checkout of the same repo, e.g. when fusesoc.conf
        # was lost. .git is a file in worktrees and submodules.
        if os.path.exists(os.path.join(library.location, ".git")):
            try:
                # Read the stored URL: get-url would apply insteadOf rewrites
                origin = subprocess.check_output(
                    [
                        "git",
                        "-C",
                        library.location,
                        "config",
                        "--get",
                        "remote.origin.url",
                    ],
                    text=True,
                ).strip()
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                raise RuntimeError(f"Cannot get origin of {library.location}: {e}")
            # git resolves a relative local origin against the checkout, not the CWD
            if os.path.isdir(os.path.join(library.location, origin)):
                origin = os.path.join(library.location, origin)
            if _normalize_uri(origin) != _normalize_uri(library.sync_uri or ""):
                raise RuntimeError(
                    f"{library.location} has origin '{origin}', "
                    f"expected '{library.sync_uri}'"
                )
            logger.info(f"Reusing existing checkout in {library.location}")
            # The checkout is left as is, so a clone's version checkout and
            # submodule update only happen on the next library update
            if library.sync_version or library.sync_submodules:
                logger.warning(
                    f"Run 'fusesoc library update {library.name}' to apply "
                    "sync-version and sync-submodules to the existing checkout"
                )
            return

        logger.info(f"Cloning library into {library.location}")
        git_args = ["clone", library.sync_uri, library.location]
        try:
            Launcher("git", git_args).run()
            Git._checkout_library_version(library)
            Git._update_library_submodules(library)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update_library(library: Library) -> None:
        download_option = "pull" if not library.sync_version else "fetch"
        git_args = ["-C", library.location, download_option]
        try:
            Git._checkout_library_version(library)
            Launcher("git", git_args).run()
            Git._update_library_submodules(library)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(str(e))

    def _checkout(self, local_dir: str) -> None:
        version = self.config.get("version", None)

        # TODO : Sanitize URL
        repo = self.config.get("repo")
        logger.info("Checking out " + repo + " to " + local_dir)
        try:
            args = [
                "clone",
                "-q",
                "--depth",
                "1",
                "--no-single-branch",
                repo,
                local_dir,
            ]
            Launcher("git", args).run()
        except RuntimeError as e:
            try:
                args = ["clone", "-q", "--no-single-branch", repo, local_dir]
                Launcher("git", args).run()
            except Exception:
                raise e
        if version:
            args = ["-C", local_dir, "checkout", "-q", version]
            Launcher("git", args).run()
