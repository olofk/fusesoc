# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
from importlib import import_module

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager, DependencyError
from fusesoc.edalizer import Edalizer
from fusesoc.librarymanager import Library, LibraryManager
from fusesoc.utils import Launcher, setup_logging, yaml_fread
from fusesoc.vlnv import Vlnv

try:
    from edalize.edatool import get_edatool
except ImportError:
    from edalize import get_edatool

logger = logging.getLogger(__name__)


class Fusesoc:
    def __init__(self, config):
        self.config = config

        self.lm = LibraryManager(config.library_root)
        self.cm = CoreManager(self.config, library_manager=self.lm)

        self._register_libraries()

    def _register_libraries(self):
        cores_root_libs = [Library(acr, acr) for acr in self.config.cores_root]
        # Add libraries from config file, env var and command-line
        for library in self.config.libraries + cores_root_libs:
            try:
                self.add_library(library)
            except (RuntimeError, OSError) as e:
                try:
                    temporary_lm = LibraryManager(self.config.library_root)
                    # try to initialize library
                    temporary_lm.add_library(library)
                    temporary_lm.update([library.name])
                    # the initialization worked, now register it properly
                    self.add_library(library)
                except (RuntimeError, OSError) as e:
                    _s = "Failed to register library '{}'"
                    logger.warning(_s.format(str(e)))

    @staticmethod
    def init_logging(verbose, monochrome, log_file=None):
        """
        Call before instantiation of fusesoc.Fusesoc or fusesoc.Config classes if logging is required.
        """
        level = logging.DEBUG if verbose else logging.INFO

        setup_logging(level, monochrome, log_file)

        if verbose:
            logger.debug("Verbose output")
        else:
            logger.debug("Concise output")

        if monochrome:
            logger.debug("Monochrome output")
        else:
            logger.debug("Colorful output")

    def add_library(self, library):
        self.cm.add_library(library, self.config.ignored_dirs)

    def get_library(self, library_name):
        return self.lm.get_library(library_name)

    def update_libraries(self, library_names):
        self.lm.update(library_names)

    def get_libraries(self):
        return self.lm.get_libraries()

    def get_core(self, name):
        return self.cm.get_core(Vlnv(name))

    def get_cores(self):
        return self.cm.get_cores()

    def find_cores(self, library):
        return self.cm.find_cores(library, self.config.ignored_dirs)

    def get_generators(self):
        return self.cm.get_generators()

    def get_work_root(self, core, flags):
        flow = core.get_flow(flags)

        target = flags["target"]

        build_root = os.path.join(self.config.build_root, core.name.sanitized_name)

        if flow:
            logger.debug(f"Using flow API (flow={flow})")
            work_root = self.config.work_root or os.path.join(build_root, target)
        else:
            logger.debug("flow not set. Falling back to tool API")
            if "tool" in flags:
                tool = flags["tool"]
            else:
                tool_error = "No flow or tool was supplied on command line or found in '{}' core description"
                raise RuntimeError(tool_error.format(core.name.sanitized_name))

            work_root = self.config.work_root or os.path.join(
                build_root, f"{target}-{tool}"
            )

        return work_root

    def get_backend(self, core, flags, backendargs=[]):

        work_root = self.get_work_root(core, flags)

        if not self.config.no_export:
            export_root = os.path.join(work_root, "src")
            logger.debug(f"Setting export_root to {export_root}")
        else:
            export_root = None

        edam_file = os.path.join(work_root, core.name.sanitized_name + ".eda.yml")

        flow = core.get_flow(flags)

        backend_class = None
        if flow:
            try:
                backend_class = getattr(
                    import_module(f"edalize.flows.{flow}"), flow.capitalize()
                )
            except ModuleNotFoundError:
                raise RuntimeError(f"Flow {flow!r} not found")
            except ImportError:
                raise RuntimeError(
                    "Selected Edalize version does not support the flow API"
                )

        else:
            try:
                backend_class = get_edatool(flags["tool"])
            except ImportError:
                raise RuntimeError(f"Backend {tool!r} not found")

        edalizer = Edalizer(
            toplevel=core.name,
            flags=flags,
            core_manager=self.cm,
            work_root=work_root,
            export_root=export_root,
            system_name=self.config.system_name,
            resolve_env_vars=self.config.resolve_env_vars_early,
        )

        try:
            edalizer.run()
            edalizer.export()
            edalizer.apply_filters(self.config.filters)
            edalizer.parse_args(backend_class, backendargs)
        except SyntaxError as e:
            raise RuntimeError(e.msg)
        except RuntimeError as e:
            raise RuntimeError("Setup failed : {}".format(str(e)))
        except DependencyError as e:
            raise RuntimeError("Failed to resolve dependencies. " + e.msg)

        if os.path.exists(edam_file):
            old_edam = yaml_fread(edam_file, self.config.resolve_env_vars_early)
        else:
            old_edam = None

        if edalizer.edam != old_edam:
            edalizer.to_yaml(edam_file)

        return edam_file, backend_class(
            edam=edalizer.edam, work_root=work_root, verbose=self.config.verbose
        )
