# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import configparser
import logging
import os
from configparser import ConfigParser as CP
from pathlib import Path

from fusesoc.librarymanager import Library

logger = logging.getLogger(__name__)


class Config:
    default_section = "main"

    def __init__(self, path=None):
        self._cp = CP(default_section=Config.default_section)

        if path is None:
            xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
                os.path.expanduser("~"), ".config"
            )
            config_files = [
                "/etc/fusesoc/fusesoc.conf",
                str(Path(xdg_config_home) / "fusesoc" / "fusesoc.conf"),
                "fusesoc.conf",
            ]
        else:
            logger.debug(f"Using config file '{path}'")
            if not os.path.isfile(path):
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, "a"):
                    pass
            config_files = [path]

        logger.debug("Looking for config files from " + ":".join(config_files))
        files_read = self._cp.read(config_files)
        logger.debug("Found config files in " + ":".join(files_read))
        self._path = files_read[-1] if files_read else None

        os.makedirs(self.cache_root, exist_ok=True)

        # Get the environment variable for further cores
        env_cores_root = []
        if os.getenv("FUSESOC_CORES"):
            env_cores_root = os.getenv("FUSESOC_CORES").split(":")
            env_cores_root.reverse()

        self.libraries = [
            Library(root, root) for root in env_cores_root
        ] + self._parse_library()

        logger.debug("cache_root=" + self.cache_root)
        logger.debug("library_root=" + self.library_root)
        logger.debug("ssh-trustfile=" + (self.ssh_trustfile or "none"))

    def _parse_library(self):
        # Parse library sections
        libraries = []
        library_sections = [x for x in self._cp.sections() if x.startswith("library")]
        for section in library_sections:
            name = section.partition(".")[2]
            try:
                location = self._cp.get(section, "location")
            except configparser.NoOptionError:
                location = os.path.join(self.library_root, name)

            try:
                auto_sync = self._cp.getboolean(section, "auto-sync")
            except configparser.NoOptionError:
                auto_sync = True
            except ValueError as e:
                _s = "Error parsing auto-sync '{}'. Ignoring library '{}'"
                logger.warning(_s.format(str(e), name))
                continue

            sync_uri = self._cp.get(section, "sync-uri", fallback=None)
            sync_version = self._cp.get(section, "sync-version", fallback=None)
            sync_type = self._cp.get(section, "sync-type", fallback=None)

            libraries.append(
                Library(name, location, sync_type, sync_uri, sync_version, auto_sync)
            )

        return libraries

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.write()

    def _resolve_path_from_cfg(self, path):
        # We only call resolve_path_from_cfg if self._cp.get(...) returned
        # something. That, in turn, only happens if we actually managed to read
        # a config file, meaning that files_read will have been nonempty in the
        # constructor and self._path will not be None.
        assert self._path is not None

        expanded = os.path.expanduser(path)
        if os.path.isabs(expanded):
            return expanded
        else:
            cfg_file_dir = os.path.dirname(os.path.realpath(self._path))
            return os.path.normpath(os.path.join(cfg_file_dir, expanded))

    def _path_from_cfg(self, name):
        as_str = self._cp.get(Config.default_section, name, fallback=None)
        return self._resolve_path_from_cfg(as_str) if as_str is not None else None

    def _paths_from_cfg(self, name):
        paths = self._cp.get(Config.default_section, name, fallback="")
        return [self._resolve_path_from_cfg(p) for p in paths.split()]

    def _get_build_root(self):
        from_cfg = self._path_from_cfg("build_root")
        if from_cfg is not None:
            return from_cfg

        return os.path.abspath("build")

    def _get_cache_root(self):
        from_cfg = self._path_from_cfg("cache_root")
        if from_cfg is not None:
            return from_cfg

        xdg_cache_home = os.environ.get("XDG_CACHE_HOME") or os.path.join(
            os.path.expanduser("~"), ".cache"
        )
        return str(Path(xdg_cache_home) / "fusesoc")

    def _get_ssh_trustfile(self):
        return self._path_from_cfg("ssh-trustfile")

    def _get_library_root(self):
        from_cfg = self._path_from_cfg("library_root")
        if from_cfg is not None:
            return from_cfg

        xdg_data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local/share"
        )
        return str(Path(xdg_data_home) / "fusesoc")

    def _get_ignored_dirs(self):
        return self._paths_from_cfg("ignored_dirs")

    def _set_default_section(self, name, val):
        self._cp.set(Config.default_section, name, str(val))

    def _arg_or_val(self, arg, val):
        if hasattr(self, arg):
            return getattr(self, arg)
        else:
            return val

    @property
    def filters(self):
        return self._cp.get(
            Config.default_section, "filters", fallback=""
        ).split() + getattr(self, "args_filters", [])

    @filters.setter
    def filters(self, val):
        self._set_default_section("filters", val)

    @property
    def build_root(self):
        return self._arg_or_val("args_build_root", self._get_build_root())

    @build_root.setter
    def build_root(self, val):
        self._set_default_section("build_root", val)

    @property
    def work_root(self):
        return self._arg_or_val("args_work_root", self._path_from_cfg("work_root"))

    @work_root.setter
    def work_root(self, val):
        self._set_default_section("work_root", val)

    @property
    def cache_root(self):
        return self._get_cache_root()

    @cache_root.setter
    def cache_root(self, val):
        self._set_default_section("cache_root", val)

    @property
    def ssh_trustfile(self):
        return self._get_ssh_trustfile()

    @ssh_trustfile.setter
    def ssh_trustfile(self, val):
        self._set_default_section("ssh-trustfile", val)

    @property
    def library_root(self):
        return self._get_library_root()

    @library_root.setter
    def library_root(self, val):
        self._set_default_section("library_root", val)

    @property
    def cores_root(self):
        return self._arg_or_val("args_cores_root", self._paths_from_cfg("cores_root"))

    @cores_root.setter
    def cores_root(self, val):
        self._set_default_section("cores_root", val)

    @property
    def ignored_dirs(self):
        return self._get_ignored_dirs()

    @ignored_dirs.setter
    def ignored_dirs(self, val):
        self._set_default_section(
            "ignored_dirs", " ".join(val) if type(val) == list else val
        )

    @property
    def resolve_env_vars_early(self):
        return self._arg_or_val(
            "args_resolve_env_vars_early",
            self._cp.getboolean(
                Config.default_section, "resolve_env_vars_early", fallback=False
            ),
        )

    @resolve_env_vars_early.setter
    def resolve_env_vars_early(self, val):
        self._set_default_section("resolve_env_vars_early", val)

    @property
    def allow_additional_properties(self):
        return self._arg_or_val(
            "args_allow_additional_properties",
            self._cp.getboolean(
                Config.default_section, "allow_additional_properties", fallback=False
            ),
        )

    @allow_additional_properties.setter
    def allow_additional_properties(self, val):
        self._set_default_section("allow_additional_properties", val)

    @property
    def verbose(self):
        # Runtime config only, not possible to set in config file
        return self._arg_or_val("args_verbose", False)

    @property
    def no_export(self):
        return self._arg_or_val(
            "args_no_export",
            self._cp.getboolean(Config.default_section, "no_export", fallback=False),
        )

    @no_export.setter
    def no_export(self, val):
        self._set_default_section("no_export", val)

    @property
    def system_name(self):
        return self._arg_or_val(
            "args_system_name",
            self._cp.get(Config.default_section, "system_name", fallback=None),
        )

    @system_name.setter
    def system_name(self, val):
        self._set_default_section("system_name", val)

    def write(self):
        conf_file_name = getattr(self, "_path", None) or "fusesoc.conf"

        with open(conf_file_name, "w") as conf_file:
            self._cp.write(conf_file)

    def add_library(self, library):
        from fusesoc.provider.provider import get_provider

        section_name = "library." + library.name

        if section_name in self._cp.sections():
            logger.warning(
                "Not adding library. {} already exists in configuration file".format(
                    library.name
                )
            )
            return

        self._cp.add_section(section_name)

        self._cp.set(section_name, "location", library.location)

        if library.sync_type:
            self._cp.set(section_name, "sync-uri", library.sync_uri)

            if library.sync_version is not None:
                self._cp.set(section_name, "sync-version", library.sync_version)

            self._cp.set(section_name, "sync-type", library.sync_type)
            _auto_sync = "true" if library.auto_sync else "false"
            self._cp.set(section_name, "auto-sync", _auto_sync)

        try:
            provider = get_provider(library.sync_type)
        except ImportError:
            raise RuntimeError("Invalid sync-type '{}'".format(library["sync-type"]))

        provider.init_library(library)

        self.write()
