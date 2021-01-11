# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import shutil
import subprocess

from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)


class Git(Provider):
    @staticmethod
    def init_library(library):
        logger.info("Cloning library into {}".format(library.location))
        git_args = ["clone", library.sync_uri, library.location]
        try:
            Launcher("git", git_args).run()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update_library(library):
        git_args = ["-C", library.location, "pull"]
        try:
            Launcher("git", git_args).run()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(str(e))

    def _checkout(self, local_dir):
        version = self.config.get("version", None)

        # TODO : Sanitize URL
        repo = self.config.get("repo")
        logger.info("Checking out " + repo + " to " + local_dir)
        args = ["clone", "-q", repo, local_dir]
        Launcher("git", args).run()
        if version:
            args = ["-C", local_dir, "checkout", "-q", version]
            Launcher("git", args).run()
