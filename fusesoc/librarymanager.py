import logging
import os

from fusesoc.provider import get_provider

logger = logging.getLogger(__name__)


class Library(object):
    def __init__(self, name, location, sync_type=None, sync_uri=None, auto_sync=True):
        if sync_type and not sync_type in ["local", "git"]:
            raise ValueError(
                "Library {} ({}) Invalid sync-type '{}'".format(
                    name, location, sync_type
                )
            )

        if sync_type in ["git"]:
            if not sync_uri:
                raise ValueError(
                    "Library {} ({}) sync-uri must be set when using sync_type 'git'".format(
                        name, location
                    )
                )

        self.name = name
        self.location = location
        self.sync_type = sync_type or "local"
        self.sync_uri = sync_uri
        self.auto_sync = auto_sync

    def update(self, force=False):
        def l(s):
            return self.name + " : " + s

        if self.sync_type == "local":
            logger.info(l("sync-type is local. Ignoring update"))
            return

        # FIXME: Do an initial checkout if missing
        if not os.path.exists(self.location):
            logger.warning(
                l("{} does not exist. Ignoring update".format(self.location))
            )
            return

        if not (self.auto_sync or force):
            logger.info(l("auto-sync disabled. Ignoring update"))
            return

        provider = get_provider(self.sync_type)
        try:
            logger.info(l("Updating..."))
            provider.update_library(self)
        except RuntimeError as e:
            logger.error(l("Failed to update library: " + str(e)))


class LibraryManager(object):
    _libraries = []

    def __init__(self, library_root):
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
                logger.warning("Could not find library {}".format(name))

        if library_names:
            force = True
        else:
            libraries = self._libraries
            force = False

        for library in libraries:
            library.update(force)
