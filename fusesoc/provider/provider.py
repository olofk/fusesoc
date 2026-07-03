# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import json
import logging
import os
import shutil
import stat
from importlib import import_module

from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

# File written inside a cached files_root after a successful checkout. Holds a
# normalised JSON copy of the provider's CAPI2 config so subsequent runs can
# detect when the user changed e.g. the provider ``version`` and the cache
# needs to be refreshed.
_CONFIG_MARKER = ".fusesoc-provider-config.json"


def get_provider(name):
    return getattr(import_module(f"fusesoc.provider.{name}"), name.capitalize())


class Provider:
    def __init__(self, config, core_root, files_root):
        self.config = config
        self.core_root = core_root
        self.files_root = files_root
        self.cachable = config.get("cachable", "") is not False
        self.patches = config.get("patches", [])

    def _config_marker_path(self):
        return os.path.join(self.files_root, _CONFIG_MARKER)

    def _config_marker_value(self):
        # Serialise with sorted keys so logically-equal configs compare equal,
        # and exclude ``cachable`` since it controls *whether* we cache, not
        # *what* we cache.
        comparable = {k: v for k, v in self.config.items() if k != "cachable"}
        return json.dumps(comparable, sort_keys=True)

    def _read_config_marker(self):
        try:
            with open(self._config_marker_path()) as f:
                return f.read()
        except OSError:
            return None

    def _write_config_marker(self):
        try:
            with open(self._config_marker_path(), "w") as f:
                f.write(self._config_marker_value())
        except OSError as e:
            # Don't fail the whole fetch over a marker write — we just lose the
            # cache-invalidation benefit on the next run.
            logger.warning(
                "Failed to write provider cache marker {}: {}".format(
                    self._config_marker_path(), e
                )
            )

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
        # Always (re-)write the marker after a successful fetch, including
        # the legacy "downloaded but no marker" case from caches predating
        # marker support.
        if self.cachable and os.path.isdir(self.files_root):
            self._write_config_marker()

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
        marker = self._read_config_marker()
        # No marker means the cache was populated by a fusesoc that predates
        # the marker (or by something else that touched the directory). Stay
        # backward-compatible: assume the cache is valid; ``fetch()`` will
        # write a fresh marker so subsequent runs can spot drift.
        if marker is not None and marker != self._config_marker_value():
            return "outofdate"
        return "downloaded"
