# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os

from fusesoc.provider.provider import get_provider
from pydantic import model_validator
from pydantic.dataclasses import dataclass
from typing_extensions import Self

logger = logging.getLogger(__name__)


@dataclass(config={"validate_assignment": True})
class Library:
    name: str
    location: str
    sync_type: str | None = None
    sync_uri: str | None = None
    sync_version: str | None = None
    auto_sync: bool = True

    @model_validator(mode="after")
    def check_instances(self) -> Self:
        if self.sync_type and not self.sync_type in ["local", "git"]:
            raise ValueError(
                "Library {} ({}) Invalid sync-type '{}'".format(
                    self.name, self.location, self.sync_type
                )
            )
        if self.sync_type in ["git"]:
            if not self.sync_uri:
                raise ValueError(
                    "Library {} ({}) sync-uri must be set when using sync_type 'git'".format(
                        self.name, self.location
                    )
                )
        return self

    def update(self, force=False):
        def l(s):
            return self.name + " : " + s

        if self.sync_type == "local":
            logger.info(l("sync-type is local. Ignoring update"))
            return

        if not (self.auto_sync or force):
            logger.info(l("auto-sync disabled. Ignoring update"))
            return

        provider = get_provider(self.sync_type)

        if not os.path.exists(self.location):
            logger.info(l(f"{self.location} does not exist. Trying a checkout"))
            try:
                provider.init_library(self)
            except RuntimeError as e:
                # Keep old behavior of logging a warning if there is a library
                # in `fusesoc.conf`, but the directory does not exist for some
                # reason and it could not be initialized.
                logger.warning(l(f"{self.location} does not exist. Ignoring update"))
            return

        try:
            logger.info(l("Updating..."))
            provider.update_library(self)
        except RuntimeError as e:
            logger.error(l("Failed to update library: " + str(e)))


class LibraryManager:
    def __init__(self, library_root):
        self._libraries = []
        self.library_root = library_root

    def add_library(self, library):
        self._libraries.append(library)

    def get_library(self, value, key="name"):
        for library in self._libraries:
            if getattr(library, key) == value:
                return library

    def get_libraries(self):
        return self._libraries

    def update(self, library_names):
        libraries = []
        for name in library_names:
            library = self.get_library(name)
            if library:
                libraries.append(library)
            else:
                logger.warning(f"Could not find library {name}")

        if library_names:
            force = True
        else:
            libraries = self._libraries
            force = False

        for library in libraries:
            library.update(force)
