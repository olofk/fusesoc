# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os
import pathlib
from itertools import chain
from types import MappingProxyType
from typing import Iterable, Mapping

from okonomiyaki.versions import EnpkgVersion
from simplesat.constraints import PrettyPackageStringParser, Requirement
from simplesat.dependency_solver import DependencySolver
from simplesat.errors import NoPackageFound, SatisfiabilityError
from simplesat.pool import Pool
from simplesat.repository import Repository
from simplesat.request import Request

from fusesoc.capi2.coreparser import Core2Parser
from fusesoc.core import Core
from fusesoc.librarymanager import LibraryManager
from fusesoc.lockfile import LockFile, LockFileMode
from fusesoc.vlnv import Vlnv, compare_relation

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    def __init__(self, value, msg=""):
        self.value = value
        self.msg = msg

    def __str__(self):
        return repr(self.value)


class CoreDB:
    _mapping: Mapping[str, str] = MappingProxyType({})

    def __init__(self):
        self._cores = {}
        self._solver_cache = {}
        self._lockfile = LockFile()

    # simplesat doesn't allow ':', '-' or leading '_'
    def _package_name(self, vlnv):
        _name = f"{vlnv.vendor}_{vlnv.library}_{vlnv.name}".lstrip("_")
        return _name.replace("-", "__")

    def _package_version(self, vlnv):
        return f"{vlnv.version}-{vlnv.revision}"

    def _parse_depend(self, depends):
        # FIXME: Handle conflicts
        deps = []

        _s = "{} {} {}"
        for d in depends:
            for simple in d.simpleVLNVs():
                deps.append(
                    _s.format(
                        self._package_name(simple),
                        simple.relation,
                        self._package_version(simple),
                    )
                )
        return ", ".join(deps)

    def _parse_virtual(self, virtuals):
        package_names = []
        for virtual in virtuals:
            for simple in virtual.simpleVLNVs():
                package_names.append("{}".format(self._package_name(simple)))
        return ", ".join(package_names)

    def add(self, core, library):
        self._solver_cache_invalidate_all()

        name = str(core.name)
        logger.debug("Adding core " + name)
        if name in self._cores:
            _s = "Replacing {} in {} with the version found in {}"
            logger.warning(
                _s.format(name, self._cores[name]["core"].core_root, core.core_root)
            )
        self._cores[name] = {"core": core, "library": library}

    def find(self, vlnv=None):
        if vlnv:
            found = self._solve(vlnv, only_matching_vlnv=True)[-1]
        else:
            found = list([core["core"] for core in self._cores.values()])
        return found

    def load_lockfile(self, filepath: pathlib.Path, disable_store: bool = False):
        mode = LockFileMode.LOAD if disable_store else LockFileMode.STORE
        self._lockfile = LockFile.load(filepath, mode)

    def store_lockfile(self, cores):
        if self._lockfile.update(cores):
            self._lockfile.store()

    def _solver_cache_lookup(self, key):
        if key in self._solver_cache:
            return self._solver_cache[key]
        return False

    def _solver_cache_store(self, key, value):
        self._solver_cache[key] = value

    def _solver_cache_invalidate(self, key):
        if key in self._solver_cache:
            del self._solver_cache[key]

    def _solver_cache_invalidate_all(self):
        self._solver_cache = {}

    def _hash_flags_dict(self, flags):
        """Hash the flags dict.

        Python's mutable sequences, like dict, are not generally hashable. For
        the dict we're using for the flags, we can simply implement hashing
        ourselves without the need to worry about nested dicts.
        """
        h = 0
        for pair in sorted(flags.items()):
            h ^= hash(pair)
        return h

    def _lockfile_replace(self, core: Vlnv):
        """Try to pin the core version from cores defined in the lock file"""
        cores = self._lockfile.cores_vlnv()
        if cores:
            for locked_core in cores:
                if locked_core.vln_str() == core.vln_str():
                    valid_version = compare_relation(locked_core, core.relation, core)
                    if valid_version:
                        core.version = locked_core.version
                        core.revision = locked_core.revision
                        core.relation = "=="
                    else:
                        # Invalid version in lockfile
                        logger.warning(
                            "Failed to pin core {} outside of dependency version {} {} {}".format(
                                str(locked_core),
                                core.vln_str(),
                                core.relation,
                                core.version,
                            )
                        )

    def _mapping_apply(self, core: Vlnv):
        """If the core matches a mapping, apply the mapping, mutating the given core."""
        remapping = self._mapping.get(core.vln_str())

        if not remapping:
            return

        previous_vlnv = str(core)
        (core.vendor, core.library, core.name) = remapping.split(":")

        logger.info(f"Mapped {previous_vlnv} to {core}.")

    def mapping_set(self, mapping_vlnvs: Iterable[str]) -> None:
        """Construct a mapping from the given cores' mappings.

        Takes the VLNV strings of the cores' mappings to apply.
        Verifies the mappings and applies them.
        """
        if self._mapping:
            raise RuntimeError(
                "Due to implementation details, mappings can only be applied once."
            )

        mappings = {}
        for mapping_vlnv in mapping_vlnvs:
            new_mapping_name = str(Vlnv(mapping_vlnv))
            new_mapping_core = self._cores.get(new_mapping_name)
            if not new_mapping_core:
                raise RuntimeError(f"The core '{mapping_vlnv}' wasn't found.")

            new_mapping_raw = new_mapping_core["core"].mapping
            if not new_mapping_raw:
                raise RuntimeError(
                    f"The core '{mapping_vlnv}' doesn't contain a mapping."
                )

            have_versions = list(
                filter(
                    lambda vlnv: (vlnv.relation, vlnv.version) != (">=", "0"),
                    map(Vlnv, chain(new_mapping_raw.keys(), new_mapping_raw.values())),
                )
            )
            if have_versions:
                raise RuntimeError(
                    "Versions cannot be given as part of a mapping."
                    f"\nThe mapping of {mapping_vlnv} following has"
                    f" the following version constraints:\n\t{have_versions}"
                )

            new_mapping = {
                Vlnv(source).vln_str(): Vlnv(destination).vln_str()
                for source, destination in new_mapping_raw.items()
            }
            new_src_set = new_mapping.keys()
            new_dest_set = frozenset(new_mapping.values())
            curr_src_set = mappings.keys()
            curr_dest_set = frozenset(mappings.values())

            new_src_dest_overlap = new_mapping.keys() & new_dest_set
            if new_src_dest_overlap:
                raise RuntimeError(
                    "Recursive mappings are not supported."
                    f"\nThe mapping {mapping_vlnv} has the following VLNV's"
                    f" in both it's sources and destinations:\n\t{new_src_dest_overlap}."
                )

            source_overlap = curr_src_set & new_src_set
            if source_overlap:
                raise RuntimeError(
                    f"The following sources are in multiple mappings:\n\t{source_overlap}."
                )

            dest_overlap = new_dest_set & curr_dest_set
            if dest_overlap:
                raise RuntimeError(
                    f"The following destinations are in multiple mappings:\n\t{dest_overlap}."
                )

            src_dest_overlap = (new_src_set | curr_src_set) & (
                new_dest_set | curr_dest_set
            )
            if src_dest_overlap:
                raise RuntimeError(
                    "Recursive mappings are not supported."
                    f"\nThe following VLNV's are in both the sources and"
                    f" destinations:\n\t{src_dest_overlap}."
                )

            mappings.update(new_mapping)

        self._mapping = MappingProxyType(mappings)

    def solve(self, top_core, flags):
        return self._solve(top_core, flags)

    def _get_conflict_map(self):
        """Return a map of cores to their conflicts

        Only one core that implements a virtual VLNV may be selected in a
        dependency tree. For each core that implements a virtual VLNV, create a
        set representing all other cores that implement one of the same virtual
        VLNVs. In the resulting package definitions, these must get "conflicts"
        constraints.
        """
        conflict_map = {}
        virtual_map = {}
        for core_data in self._cores.values():
            core = core_data["core"]
            _virtuals = core.get_virtuals()
            for virtual in _virtuals:
                for simple in virtual.simpleVLNVs():
                    virtual_pkg = self._package_name(simple)
                    # FIXME: The real package should include version info
                    real_pkg = self._package_name(core.name)
                    virtual_set = virtual_map.setdefault(virtual_pkg, set())
                    virtual_set.add(real_pkg)
        for virtual_pkg, virtual_set in virtual_map.items():
            for real_pkg in virtual_set:
                conflict_set = conflict_map.setdefault(real_pkg, set())
                conflict_set |= virtual_set
        for real_pkg, conflict_set in conflict_map.items():
            conflict_set.remove(real_pkg)
        return conflict_map

    def _solve(self, top_core, flags={}, only_matching_vlnv=False):
        def eq_vln(this, that):
            return (
                this.vendor == that.vendor
                and this.library == that.library
                and this.name == that.name
            )

        # Try to return a cached result
        solver_cache_key = (top_core, self._hash_flags_dict(flags), only_matching_vlnv)
        cached_solution = self._solver_cache_lookup(solver_cache_key)
        if cached_solution:
            return cached_solution

        repo = Repository()
        _flags = flags.copy()
        cores = [x["core"] for x in self._cores.values()]
        conflict_map = self._get_conflict_map()

        for core in cores:
            if only_matching_vlnv:
                if not any(
                    [eq_vln(core.name, top_core)]
                    + [
                        eq_vln(virtual_vlnv, top_core)
                        for virtual_vlnv in core.get_virtuals(_flags)
                    ]
                ):
                    continue

            # Build a "pretty" package string in a format expected by
            # PrettyPackageStringParser()
            package_str = "{} {}-{}".format(
                self._package_name(core.name),
                core.name.version,
                core.name.revision,
            )

            _virtuals = core.get_virtuals(_flags)
            if _virtuals:
                _s = "; provides ( {} )"
                package_str += _s.format(self._parse_virtual(_virtuals))
            conflict_set = conflict_map.get(self._package_name(core.name), set())
            if len(conflict_set) > 0:
                _s = "; conflicts ( {} )"
                package_str += _s.format(", ".join(list(conflict_set)))

            # Add dependencies only if we want to build the whole dependency
            # tree.
            if not only_matching_vlnv:
                _flags["is_toplevel"] = core.name == top_core
                _depends = core.get_depends(_flags)
                if _depends:
                    for depend in _depends:
                        self._mapping_apply(depend)
                        self._lockfile_replace(depend)
                    _s = "; depends ( {} )"
                    package_str += _s.format(self._parse_depend(_depends))
            else:
                self._lockfile_replace(top_core)

            parser = PrettyPackageStringParser(EnpkgVersion.from_string)

            package = parser.parse_to_package(package_str)
            package.core = core

            repo.add_package(package)

        request = Request()
        _top_dep = "{} {} {}".format(
            self._package_name(top_core),
            top_core.relation,
            self._package_version(top_core),
        )
        request.install(Requirement._from_string(_top_dep))

        installed_repository = Repository()
        pool = Pool([repo])
        pool.add_repository(installed_repository)
        solver = DependencySolver(pool, [repo], installed_repository)

        try:
            transaction = solver.solve(request)
        except SatisfiabilityError as e:
            raise DependencyError(top_core.name, msg=e.unsat.to_string(pool))
        except NoPackageFound as e:
            raise DependencyError(top_core.name)

        virtual_selection = {}
        partial_lockfile = False
        objdict = {}
        if len(transaction.operations) > 1:
            for op in transaction.operations:
                package_name = self._package_name(op.package.core.name)
                virtuals = op.package.core.get_virtuals(_flags)
                for p in op.package.provides:
                    for virtual in virtuals:
                        if p[0] == self._package_name(virtual):
                            # Add virtual core selection to dictionary
                            virtual_selection[package_name] = (
                                op.package.core.name,
                                virtual,
                            )
                    objdict[p[0]] = str(op.package.core.name)
                for p in op.package.install_requires:
                    if p[0] in virtual_selection:
                        # If package that implements a virtual core is required, remove from the dictionary
                        del virtual_selection[p[0]]
                if not self._lockfile.core_vlnv_exists(op.package.core.name):
                    partial_lockfile = True
                op.package.core.direct_deps = [
                    objdict[n[0]] for n in op.package.install_requires
                ]
        # Print a warning for all virtual selections that has no concrete requirement selection
        for virtual in virtual_selection.values():
            logger.warning(
                "Non-deterministic selection of virtual core {} selected {}".format(
                    virtual[1], virtual[0]
                )
            )
        if partial_lockfile and not self._lockfile.no_cores():
            logger.warning("Using lock file with partial list of cores")

        result = [op.package.core for op in transaction.operations]

        # Cache the solution for further lookups
        self._solver_cache_store(solver_cache_key, result)

        return result


class CoreManager:
    def __init__(self, config, library_manager=None):
        self.config = config
        self.db = CoreDB()
        self._lm = (
            LibraryManager(config.library_root)
            if library_manager == None
            else library_manager
        )
        self.core2parser = Core2Parser(
            config.resolve_env_vars_early, config.allow_additional_properties
        )

    def find_cores(self, library, ignored_dirs):
        found_cores = []
        path = os.path.expanduser(library.location)
        exclude = {".git"}
        if os.path.isdir(path) == False:
            raise OSError(path + " is not a directory")
        logger.debug("Checking for cores in " + path)
        visited = set()
        for root, dirs, files in os.walk(path, followlinks=True):
            ignore_tree = ("FUSESOC_IGNORE" in files) or (
                os.path.realpath(root) in ignored_dirs
            )
            if ignore_tree:
                del dirs[:]
                continue

            keep_dirs = []
            for _d in dirs:
                # Ignore sub dirs in the exclude set
                if _d in exclude:
                    continue

                st = os.stat(os.path.join(root, _d))
                dirkey = st.st_dev, st.st_ino
                # Ignore dirs we already visited. Protects against endless symlink recursion
                if dirkey in visited:
                    continue

                visited.add(dirkey)
                keep_dirs.append(_d)

            dirs[:] = keep_dirs

            for f in files:
                if f.endswith(".core"):
                    core_file = os.path.join(root, f)
                    try:
                        capi_version = self._detect_capi_version(core_file)
                        if capi_version == 1:
                            # Skip core files which are not in CAPI2 format.
                            logger.error(
                                "Core file {} is in CAPI1 format, which is not supported "
                                "any more since FuseSoC 2.0. The core file is ignored. "
                                "Please migrate your cores to the CAPI2 file format, or "
                                "use FuseSoC 1.x as stop-gap.".format(core_file)
                            )
                            continue
                        elif capi_version == -1:
                            # Skip core files which are not FuseSoc format at all.
                            continue

                        core = Core(
                            parser=self.core2parser,
                            core_file=core_file,
                            cache_root=self.config.cache_root,
                        )
                        found_cores.append(core)
                    except SyntaxError as e:
                        w = "Parse error. Ignoring file " + core_file + ": " + e.msg
                        logger.warning(w)
                    except ImportError as e:
                        w = 'Failed to register "{}" due to unknown provider: {}'
                        logger.warning(w.format(core_file, str(e)))
                    except ValueError as e:
                        logger.warning(e)
        return found_cores

    def _detect_capi_version(self, core_file) -> int:
        """Detect the CAPI version in a .core file

        Returns:
            Version of the core file (1 or 2)
        """
        try:
            with open(core_file) as f:
                l = f.readline().split()
                if l:
                    first_line = l[0]
                else:
                    first_line = ""
                if first_line == "CAPI=1":
                    return 1
                elif first_line == "CAPI=2:":
                    return 2
                else:
                    error_msg = (
                        "The first line of the core file {} must be "
                        ' "CAPI=1" or "CAPI=2:".'.format(core_file)
                    )
                    error_msg += '  The first line of this core file is "{}".'.format(
                        first_line
                    )
                    if first_line == "CAPI=2":
                        error_msg += "  Just add a colon on the end!"
                    logger.warning(error_msg)
                    raise ValueError(
                        "Unable to determine CAPI version from core file {}.".format(
                            core_file
                        )
                    )
        except Exception as error:
            error_msg = f"Unable to determine CAPI version from core file {core_file}"
            logger.warning(error_msg)
            return -1

    def _load_cores(self, library, ignored_dirs):
        found_cores = self.find_cores(library, ignored_dirs)
        for core in found_cores:
            self.db.add(core, library)

    def add_library(self, library, ignored_dirs):
        """Register a library"""
        abspath = os.path.abspath(os.path.expanduser(library.location))
        _library = self._lm.get_library(abspath, "location")
        if _library:
            _s = "Not adding library {} ({}). Library {} already registered for this location"
            logger.warning(_s.format(library.name, abspath, _library.name))
            return

        self._load_cores(library, ignored_dirs)
        self._lm.add_library(library)

    def get_libraries(self):
        """Get all registered libraries"""
        return self._lm.get_libraries()

    def get_depends(self, core, flags):
        """Get an ordered list of all dependencies of a core

        All direct and indirect dependencies are resolved into a dependency
        tree, the tree is flattened, and an ordered list of dependencies is
        created.

        The first element in the list is a leaf dependency, the last element
        is the core at the root of the dependency tree.
        """
        logger.debug(
            "Calculating dependencies for {}{} with flags {}".format(
                core.relation, str(core), str(flags)
            )
        )
        resolved_core = self.db.find(core)
        deps = self.db.solve(resolved_core.name, flags)
        logger.debug(" Resolved core to {}".format(str(resolved_core.name)))
        logger.debug(" with dependencies " + ", ".join([str(c.name) for c in deps]))
        return deps

    def get_cores(self):
        """Get a dict with all cores, indexed by the core name"""
        return {str(x.name): x for x in self.db.find()}

    def get_core(self, name):
        """Get a core with a given name"""
        c = self.db.find(name)
        c.name.relation = "=="
        return c

    def get_generators(self):
        """Get a dict with all registered generators, indexed by name"""
        generators = {}
        for core in self.db.find():
            if hasattr(core, "get_generators"):
                _generators = core.get_generators()
                if _generators:
                    generators[str(core.name)] = _generators
        return generators
