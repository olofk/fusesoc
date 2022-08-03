# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import configparser
import logging
import os
from configparser import ConfigParser as CP

from fusesoc.librarymanager import Library

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, path=None):
        config = CP()

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
            logger.debug(f"Using config file '{path}'")
            if not os.path.isfile(path):
                with open(path, "a"):
                    pass
            config_files = [path]

        logger.debug("Looking for config files from " + ":".join(config_files))
        files_read = config.read(config_files)
        logger.debug("Found config files in " + ":".join(files_read))
        self._path = files_read[-1] if files_read else None

        self.build_root = self._get_build_root(config)
        self.cache_root = self._get_cache_root(config)
        cores_root = self._get_cores_root(config)
        systems_root = self._get_systems_root(config)
        self.library_root = self._get_library_root(config)
        self.ignored_dirs = self._get_ignored_dirs(config)

        os.makedirs(self.cache_root, exist_ok=True)

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

        all_core_roots = cores_root + systems_root + env_cores_root

        self.libraries = [Library(root, root) for root in all_core_roots] + libraries

        logger.debug("cache_root=" + self.cache_root)
        logger.debug("library_root=" + self.library_root)

    def _resolve_path_from_cfg(self, path):
        # We only call resolve_path_from_cfg if config.get(...) returned
        # something. That, in turn, only happens if we actually managed to read
        # a config file, meaning that files_read will have been nonempty in the
        # constructor and self._path will not be None.
        assert self._path is not None

        expanded = os.path.expanduser(path)
        if os.path.isabs(expanded):
            return expanded
        else:
            cfg_file_dir = os.path.dirname(self._path)
            return os.path.join(cfg_file_dir, expanded)

    def _path_from_cfg(self, config, name):
        as_str = config.get("main", name, fallback=None)
        return self._resolve_path_from_cfg(as_str) if as_str is not None else None

    def _paths_from_cfg(self, config, name):
        paths = config.get("main", name, fallback="")
        return [self._resolve_path_from_cfg(p) for p in paths.split()]

    def _get_build_root(self, config):
        from_cfg = self._path_from_cfg(config, "build_root")
        if from_cfg is not None:
            return from_cfg

        return os.path.abspath("build")

    def _get_cache_root(self, config):
        from_cfg = self._path_from_cfg(config, "cache_root")
        if from_cfg is not None:
            return from_cfg

        xdg_cache_home = os.environ.get("XDG_CACHE_HOME") or os.path.join(
            os.path.expanduser("~"), ".cache"
        )
        return os.path.join(xdg_cache_home, "fusesoc")

    def _get_cores_root(self, config):
        from_cfg = self._paths_from_cfg(config, "cores_root")
        if from_cfg:
            logger.warning(
                "The cores_root option in fusesoc.conf is deprecated. "
                "Please migrate to libraries instead"
            )
            return from_cfg

        return [os.path.abspath("cores")] if os.path.exists("cores") else []

    def _get_systems_root(self, config):
        from_cfg = self._paths_from_cfg(config, "systems_root")
        if from_cfg:
            logger.warning(
                "The systems_root option in fusesoc.conf is deprecated. "
                "Please migrate to libraries instead"
            )
            return from_cfg

        return [os.path.abspath("systems")] if os.path.exists("systems") else []

    def _get_library_root(self, config):
        from_cfg = self._path_from_cfg(config, "library_root")
        if from_cfg is not None:
            return from_cfg

        xdg_data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local/share"
        )
        return os.path.join(xdg_data_home, "fusesoc")

    def _get_ignored_dirs(self, config):
        return self._paths_from_cfg(config, "ignored_dirs")

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
        except ImportError:
            raise RuntimeError("Invalid sync-type '{}'".format(library["sync-type"]))

        provider.init_library(library)

        with open(self._path, "w") as conf_file:
            config.write(conf_file)
