# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause


class Library:
    """FuseSoC library."""

    def __init__(
        self,
        name: str,
        location: str,
        sync_type: str | None = None,
        sync_uri: str | None = None,
        sync_version: str | None = None,
        auto_sync: bool = True,
        sync_submodules: bool = False,
    ) -> None:
        """Create a new instance of FuseSoC library.

        Args:
            name: Name of library.
            location: Path to library directory.
            sync_type: Type of library synchronization.
            sync_uri: URI to remote library.
            sync_version: Version of library to synchronize during library updates.
            auto_sync: If set to :data:`True` then it will automatically synchronize library.
            sync_submodules: If set to :data:`True` then it will also clone/fetch git submodules.
        """
        self.name = name
        self.location = location
        self.sync_type = sync_type or "local"
        self.sync_uri = sync_uri
        self.sync_version = sync_version
        self.auto_sync = auto_sync
        self.sync_submodules = sync_submodules
