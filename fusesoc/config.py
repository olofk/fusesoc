# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import configparser
import logging
import os
import sys
from configparser import ConfigParser as CP

from fusesoc.librarymanager import Library

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, path=None, file=None):
        self.build_root = None
        self.cache_root = None
        cores_root = []
        systems_root = []
        self.library_root = None
        self.libraries = []

        config = CP()
        if file is None:
            if path is None:
                xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
                    os.path.expanduser("~"), ".config"
                )
                config_files = [
                    "/etc/fusesoc/fusesoc.conf",
                    os.path.join(xdg_config_home, "fusesoc", "fusesoc.conf"),
                    "fusesoc.conf",
                ]
            else:
                logger.debug("Using config file '{}'".format(path))
                if not os.path.isfile(path):
                    with open(path, "a"):
                        pass
                config_files = [path]

            logger.debug("Looking for config files from " + ":".join(config_files))
            files_read = config.read(config_files)
            logger.debug("Found config files in " + ":".join(files_read))
            if files_read:
                self._path = files_read[-1]
        else:
            logger.debug("Using supplied config file")
            if sys.version[0] == "2":
                config.readfp(file)
            else:
                config.read_file(file)
            file.seek(0)
            self._path = file.name

        for item in ["build_root", "cache_root", "systems_root", "library_root"]:
            try:
                setattr(self, item, os.path.expanduser(config.get("main", item)))
                if item == "systems_root":
                    systems_root = [os.path.expanduser(config.get("main", item))]
                    logger.warning(
                        "The systems_root option in fusesoc.conf is deprecated. Please migrate to libraries instead"
                    )
            except configparser.NoOptionError:
                pass
            except configparser.NoSectionError:
                pass

        try:
            cores_root = config.get("main", "cores_root").split()
            logger.warning(
                "The cores_root option in fusesoc.conf is deprecated. Please migrate to libraries instead"
            )
        except configparser.NoOptionError:
            pass
        except configparser.NoSectionError:
            pass

        # Set fallback values
        if self.build_root is None:
            self.build_root = os.path.abspath("build")
        if self.cache_root is None:
            xdg_cache_home = os.environ.get("XDG_CACHE_HOME") or os.path.join(
                os.path.expanduser("~"), ".cache"
            )
            self.cache_root = os.path.join(xdg_cache_home, "fusesoc")
            os.makedirs(self.cache_root, exist_ok=True)
        if not cores_root and os.path.exists("cores"):
            cores_root = [os.path.abspath("cores")]
        if (not systems_root) and os.path.exists("systems"):
            systems_root = [os.path.abspath("systems")]
        if self.library_root is None:
            xdg_data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
                os.path.expanduser("~"), ".local/share"
            )
            self.library_root = os.path.join(xdg_data_home, "fusesoc")

        # Parse library sections
        libraries = []
        library_sections = [x for x in config.sections() if x.startswith("library")]
        for section in library_sections:
            name = section.partition(".")[2]
            try:
                location = config.get(section, "location")
            except configparser.NoOptionError:
                location = os.path.join(self.library_root, name)

            try:
                auto_sync = config.getboolean(section, "auto-sync")
            except configparser.NoOptionError:
                auto_sync = True
            except ValueError as e:
                _s = "Error parsing auto-sync '{}'. Ignoring library '{}'"
                logger.warning(_s.format(str(e), name))
                continue

            try:
                sync_uri = config.get(section, "sync-uri")
            except configparser.NoOptionError:
                # sync-uri is absent for local libraries
                sync_uri = None

            try:
                sync_type = config.get(section, "sync-type")
            except configparser.NoOptionError:
                # sync-uri is absent for local libraries
                sync_type = None
            libraries.append(Library(name, location, sync_type, sync_uri, auto_sync))
        # Get the environment variable for further cores
        env_cores_root = []
        if os.getenv("FUSESOC_CORES"):
            env_cores_root = os.getenv("FUSESOC_CORES").split(":")
            env_cores_root.reverse()

        for root in cores_root + systems_root + env_cores_root:
            self.libraries.append(Library(root, root))

        self.libraries += libraries

        logger.debug("cache_root=" + self.cache_root)
        logger.debug("library_root=" + self.library_root)

    def add_library(self, library):
        from fusesoc.provider import get_provider

        if not hasattr(self, "_path"):
            raise RuntimeError("No FuseSoC config file found - can't add library")
        section_name = "library." + library.name

        config = CP()
        config.read(self._path)

        if section_name in config.sections():
            logger.warning(
                "Not adding library. {} already exists in configuration file".format(
                    library.name
                )
            )
            return

        config.add_section(section_name)

        config.set(section_name, "location", library.location)

        if library.sync_type:
            config.set(section_name, "sync-uri", library.sync_uri)
            config.set(section_name, "sync-type", library.sync_type)
            _auto_sync = "true" if library.auto_sync else "false"
            config.set(section_name, "auto-sync", _auto_sync)

        try:
            provider = get_provider(library.sync_type)
        except ImportError as e:
            raise RuntimeError("Invalid sync-type '{}'".format(library["sync-type"]))

        provider.init_library(library)

        with open(self._path, "w") as conf_file:
            config.write(conf_file)
