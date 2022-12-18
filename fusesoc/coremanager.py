# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os

from okonomiyaki.versions import EnpkgVersion
from simplesat.constraints import PrettyPackageStringParser, Requirement
from simplesat.dependency_solver import DependencySolver
from simplesat.errors import NoPackageFound, SatisfiabilityError
from simplesat.pool import Pool
from simplesat.repository import Repository
from simplesat.request import Request

from fusesoc.core import Core
from fusesoc.librarymanager import LibraryManager

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    def __init__(self, value, msg=""):
        self.value = value
        self.msg = msg

    def __str__(self):
        return repr(self.value)


class CoreDB:
    def __init__(self):
        self._cores = {}
        self._solver_cache = {}

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
            logger.debug(
                _s.format(name, self._cores[name]["core"].core_root, core.core_root)
            )
        self._cores[name] = {"core": core, "library": library}

    def find(self, vlnv=None):
        if vlnv:
            found = self._solve(vlnv, only_matching_vlnv=True)[-1]
        else:
            found = list([core["core"] for core in self._cores.values()])
        return found

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

    def solve(self, top_core, flags):
        return self._solve(top_core, flags)

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
        for core in cores:
            if only_matching_vlnv:
                if not any(
                    [eq_vln(core.name, top_core)]
                    + [
                        eq_vln(virtual_vlnv, top_core)
                        for virtual_vlnv in core.get_virtuals()
                    ]
                ):
                    continue

            # Build a "pretty" package string in a format expected by
            # PrettyPackageStringParser()
            package_str = "{} {}-{}".format(
                self._package_name(core.name), core.name.version, core.name.revision
            )

            _virtuals = core.get_virtuals()
            if _virtuals:
                _s = "; provides ( {} )"
                package_str += _s.format(self._parse_virtual(_virtuals))

            # Add dependencies only if we want to build the whole dependency
            # tree.
            if not only_matching_vlnv:
                _flags["is_toplevel"] = core.name == top_core
                _depends = core.get_depends(_flags)
                if _depends:
                    _s = "; depends ( {} )"
                    package_str += _s.format(self._parse_depend(_depends))

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

        objdict = {}
        if len(transaction.operations) > 1:
            for op in transaction.operations:
                for p in op.package.provides:
                    objdict[p[0]] = str(op.package.core.name)
                op.package.core.direct_deps = [
                    objdict[n[0]] for n in op.package.install_requires
                ]
        result = [op.package.core for op in transaction.operations]

        # Cache the solution for further lookups
        self._solver_cache_store(solver_cache_key, result)

        return result


class CoreManager:
    def __init__(self, config):
        self.config = config
        self.db = CoreDB()
        self._lm = LibraryManager(config.library_root)

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
                os.path.abspath(root) in ignored_dirs
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
                            core_file,
                            self.config.cache_root,
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
