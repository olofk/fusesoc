# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import shutil
import stat

from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)


class Provider:
    def __init__(self, config, core_root, files_root):
        self.config = config
        self.core_root = core_root
        self.files_root = files_root
        self.cachable = not (config.get("cachable", "") == False)
        self.patches = config.get("patches", [])

    def clean_cache(self):
        def _make_tree_writable(topdir):
            # Ensure all files and directories under topdir are writable
            # (and readable) by owner.
            for d, _, files in os.walk(topdir):
                os.chmod(d, os.stat(d).st_mode | stat.S_IWRITE | stat.S_IREAD)
                for fname in files:
                    fpath = os.path.join(d, fname)
                    if os.path.isfile(fpath):
                        os.chmod(
                            fpath, os.stat(fpath).st_mode | stat.S_IWRITE | stat.S_IREAD
                        )

        if os.path.exists(self.files_root):
            _make_tree_writable(self.files_root)
            shutil.rmtree(self.files_root)

    def fetch(self):
        status = self.status()
        if status == "empty":
            self._checkout(self.files_root)
            _fetched = True
        elif status == "outofdate":
            self.clean_cache()
            self._checkout(self.files_root)
            _fetched = True
        elif status == "downloaded":
            _fetched = False
        else:
            raise RuntimeError(
                "Provider status is: '" + status + "'. This shouldn't happen"
            )
        if _fetched:
            self._patch()

    def _patch(self):
        for f in self.patches:
            patch_file = os.path.abspath(os.path.join(self.core_root, f))
            if os.path.isfile(patch_file):
                logger.debug(
                    "  applying patch file: "
                    + patch_file
                    + "\n"
                    + "                   to: "
                    + os.path.join(self.files_root)
                )
                try:
                    Launcher("git", ["apply", patch_file], self.files_root).run()
                except OSError:
                    raise RuntimeError("Failed to call 'git' for patching core")

    def status(self):
        if not self.cachable:
            return "outofdate"
        if not os.path.isdir(self.files_root):
            return "empty"
        else:
            return "downloaded"
