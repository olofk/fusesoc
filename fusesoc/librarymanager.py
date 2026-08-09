# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
from collections.abc import Iterable

from fusesoc.library import Library
from fusesoc.provider.provider import Provider, get_provider

logger = logging.getLogger(__name__)


class LibraryManager:
    """Manager to manage libraries. A library is an abstracted collection of FuseSoC cores."""

    def __init__(self) -> None:
        """Create a new instance of library manager to manage libraries."""
        self._libraries: dict[str, Library] = {}
        """List of registered libraries."""

    def add_library(self, library: Library) -> None:
        """Add library to manager.

        Args:
            library: The library object.
        """
        self._libraries[library.name] = library

    def get_library(self, value: str, key: str | None = None) -> Library | None:
        """Get library from manager.

        Args:
            name: Name of library.
            key: Find library based on key.

        Returns:
            Library if found. Otherwise :data:`None` if not.
        """
        if key and key != "name":
            # Slow path
            for library in self._libraries.values():
                if getattr(library, key, None) == value:
                    return library

            return None

        # Fast path
        return self._libraries.get(value)

    def get_libraries(self) -> list[Library]:
        """Get list of libraries.

        Returns:
            List of libraries.
        """
        return list(self._libraries.values())

    def update(self, library_names: Iterable[str] | None = None) -> None:
        """Update libraries.

        Args:
            library_names: List of libraries to update. If not provided or empty, update all libraries.
        """
        if library_names:
            for name in library_names:
                library: Library | None = self._libraries.get(name)

                if library:
                    self._update_library(library, force=True)
                else:
                    logger.warning("%s : Could not find library", name)
        else:
            for library in self._libraries.values():
                self._update_library(library, force=False)

    def _update_library(self, library: Library, force: bool = False) -> None:
        """Update library.

        Args:
            library: Library that will be updated.
            force: Force library update.
        """
        if library.sync_type == "local":
            logger.info("%s : sync-type is local. Ignoring update", library.name)
            return

        if not (library.auto_sync or force):
            logger.info("%s : auto-sync disabled. Ignoring update", library.name)
            return

        provider: Provider = get_provider(library.sync_type)

        if not library.location:
            logger.error("%s : location to library was not specified", library.name)
            return

        if not library.sync_uri:
            logger.error("%s : sync-uri to library was not specified", library.name)
            return

        if os.path.exists(library.location):
            logger.info("%s : Updating...", library.name)
            try:
                provider.update_library(library)
            except RuntimeError as e:
                logger.error(
                    "%s : %s Failed to update library: %s",
                    library.name,
                    library.location,
                    e,
                )
        else:
            logger.info(
                "%s : %s does not exist. Trying to initialize library",
                library.name,
                library.location,
            )
            try:
                provider.init_library(library)
            except RuntimeError as e:
                logger.error(
                    "%s : %s Failed to initialize library: %s",
                    library.name,
                    library.location,
                    e,
                )
