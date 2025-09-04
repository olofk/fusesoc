# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import subprocess
from typing import Callable

from fusesoc.librarymanager import Library
from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)


class Env(Provider):
    """A provider for cores in locations special to the environment."""

    def _resolve_poetry(library: Library) -> str:
        logger.info(f"Looking for Poetry environment for library {library.name}")

        err = False
        envpath = None
        try:
            # We need to wrap Poetry in Poetry in case the environment uses a different
            # Python interpreter than is currently configured through `poetry env use`. If
            # the two differ, then `poetry env info -p` just gives us a blank path.
            proc = Launcher("poetry", ["run", "poetry", "env", "info", "--path"])
            proc = proc.run(stdout=subprocess.PIPE)
            stdout, _ = proc.communicate()
            envpath = stdout.decode("ascii").strip()
        except subprocess.CalledProcessError as e:
            logger.error("Failed to run `poetry env info`")
            err = True

        if envpath and len(envpath) == 0:
            logger.error("Poetry returned an empty environment path")
            err = True

        if err:
            raise RuntimeError("Could not create library from Poetry environment")

        logger.info(f"Using '{envpath}'")
        return envpath

    _SYNC_URIS = {"poetry": _resolve_poetry}

    @staticmethod
    def resolve(library: Library) -> str:
        resolver = Env._SYNC_URIS.get(library.sync_uri, None)
        if not resolver:
            raise RuntimeError(
                "Unsupported sync-uri '{}' for sync-type 'env', options are: {}".format(
                    library.sync_uri, Env._SYNC_URIS.keys()
                )
            )

        return resolver(library)

    @staticmethod
    def init_library(library):
        path = Env.resolve(library)

        library.location = None
        if not library.auto_sync:
            logger.info("Auto-sync disabled, converting to local provider")
            library.location = path
            library.sync_type = "local"
            library.sync_uri = path

    def _checkout(self, local_dir):
        pass

    @staticmethod
    def update_library(library):
        pass
