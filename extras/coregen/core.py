#!/usr/bin/env python3

import os, argparse, subprocess, logging
from fusesoc.main import _get_core, init_coremanager
from fusesoc.config import Config
from fusesoc.coremanager import DependencyError
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# TODO:
#  - add support for modifying the current absolute file paths to ones relative
#    to the $PROJ_HOME environment variable. This would allow portability of VC
#    files but perhaps it's better to force auto-generation for each flow?
# -----------------------------------------------------------------------------

class CoreDeps(object):
    """Fusesoc dependency builder.

    This class borrows much of the FuseSoC front end dependency
    tree builder in order to reuse the Core file for EDA tool
    flows outside of FuseSoC.

    Class methods provide access to files, directories and paths
    that will be useful to construct tool flows re-using the
    existing core files.
    """
    def __init__(self, core_name: str, cores_root: str, flags: Dict):
        self.core_manager = init_coremanager(Config(), cores_root)
        self.core = _get_core(self.core_manager, core_name)
        self.toplevel_vlnv = self.core.name
        try:
            tool = self.core.get_tool(flags)
        except SyntaxError as e:
            logger.error(e.msg)
            exit(1)
        flags['tool'] = tool
        self.flags = flags

    @property
    def resolved_cores(self):
        """ Get a list of all "used" cores after the dependency resolution """
        try:
            return self.core_manager.get_depends(self.toplevel_vlnv, self.flags)
        except DependencyError as e:
            logger.error(
                e.msg + "\nFailed to resolve dependencies for {}".format(self.toplevel_vlnv)
            )
            exit(1)
        except SyntaxError as e:
            logger.error(e.msg)
            exit(1)

    @property
    def include_files(self):
        """ Get a list of all include files in the design """
        includes = []
        for core in self.resolved_cores:
            for file in core.get_files(self.flags):
                if 'is_include_file' in file.keys() and file['is_include_file']:
                    includes += [ os.path.join( core.core_root, file['name'] ) ]
        return includes

    @property
    def include_dirs(self):
        """Get a list of all include directories for the core"""
        return list( set( [os.path.dirname(file) for file in self.include_files] ) )

    @property
    def source_files(self):
        """ Get a list of source files """
        sources = []
        for core in self.resolved_cores:
            for file in core.get_files(self.flags):
                if 'is_include_file' not in file.keys():
                    sources += [ os.path.join( core.core_root, file['name'] ) ]
        return sources

    @property
    def toplevel(self):
        return self.core.get_toplevel(self.flags)
