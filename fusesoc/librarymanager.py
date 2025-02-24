# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
from typing import Literal

from fusesoc.provider.provider import get_provider
from pydantic import model_validator
from pydantic.dataclasses import dataclass
from typing_extensions import Self

logger = logging.getLogger(__name__)


@dataclass(config={"validate_assignment": True})
class Library:
    name: str
    location: str
    sync_type: Literal["local", "git", "url"] | None = None
    sync_uri: str | None = None
    sync_version: str | None = None
    auto_sync: bool = True

    @model_validator(mode="after")
    def check_instances(self) -> Self:
        if self.sync_type and self.sync_type not in ("local", "git", "url"):
            raise ValueError(
                "Library {} ({}) Invalid sync-type '{}'".format(
                    self.name, self.location, self.sync_type
                )
            )
        if self.sync_type in ("git", "url"):
            if self.sync_uri is None:
                raise ValueError(
                    f"Library {self.name} ({self.location}) 'sync_uri' must be set when using sync_type '{self.sync_type}'"
                )
        return self

    def update(self, force=False):
        def lib(s):
            return self.name + " : " + s

        if self.sync_type == "local":
            logger.info(lib("sync-type is local. Ignoring update"))
            return

        if not (self.auto_sync or force):
            logger.info(lib("auto-sync disabled. Ignoring update"))
            return

        provider = get_provider(self.sync_type)

        if not os.path.exists(self.location):
            logger.info(lib(f"{self.location} does not exist. Trying a checkout"))
            try:
                provider.init_library(self)
            except RuntimeError:
                # Keep old behavior of logging a warning if there is a library
                # in `fusesoc.conf`, but the directory does not exist for some
                # reason and it could not be initialized.
                logger.warning(lib(f"{self.location} does not exist. Ignoring update"))
            return

        try:
            logger.info(lib("Updating..."))
            provider.update_library(self)
        except RuntimeError as e:
            logger.error(lib("Failed to update library: " + str(e)))


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
