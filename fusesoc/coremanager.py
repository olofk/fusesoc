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


class CoreDB(object):
    def __init__(self):
        self._cores = {}

    # simplesat doesn't allow ':', '-' or leading '_'
    def _package_name(self, vlnv):
        _name = "{}_{}_{}".format(vlnv.vendor, vlnv.library, vlnv.name).lstrip("_")
        return _name.replace("-", "__")

    def _package_version(self, vlnv):
        return "{}-{}".format(vlnv.version, vlnv.revision)

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

    def add(self, core, library):
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

    def solve(self, top_core, flags):
        return self._solve(top_core, flags)

    def _solve(self, top_core, flags={}, only_matching_vlnv=False):
        def eq_vln(this, that):
            return (
                this.vendor == that.vendor
                and this.library == that.library
                and this.name == that.name
            )

        repo = Repository()
        _flags = flags.copy()
        cores = [x["core"] for x in self._cores.values()]
        for core in cores:
            if only_matching_vlnv:
                if not eq_vln(core.name, top_core):
                    continue

            package_str = "{} {}-{}".format(
                self._package_name(core.name), core.name.version, core.name.revision
            )
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
        simplevlnvs = top_core.simpleVLNVs()
        for sv in simplevlnvs:
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
        depdict = {}
        if len(transaction.operations) > 1:
            for op in transaction.operations:
                objdict[op.package._name] = str(op.package.core.name)
                depdict[str(op.package.core.name)] = [
                    objdict[n[0]] for n in op.package.install_requires
                ]
                op.package.core.direct_deps = [
                    objdict[n[0]] for n in op.package.install_requires
                ]
        return [op.package.core for op in transaction.operations]


class CoreManager(object):
    def __init__(self, config):
        self.config = config
        self.db = CoreDB()
        self._lm = LibraryManager(config.library_root)

    def load_cores(self, library):
        path = os.path.expanduser(library.location)
        if os.path.isdir(path) == False:
            raise IOError(path + " is not a directory")
        logger.debug("Checking for cores in " + path)
        for root, dirs, files in os.walk(path, followlinks=True):
            if "FUSESOC_IGNORE" in files:
                del dirs[:]
                continue
            for f in files:
                if f.endswith(".core"):
                    core_file = os.path.join(root, f)
                    try:
                        core = Core(core_file, self.config.cache_root)
                        self.db.add(core, library)
                    except SyntaxError as e:
                        w = "Parse error. Ignoring file " + core_file + ": " + e.msg
                        logger.warning(w)
                    except ImportError as e:
                        w = 'Failed to register "{}" due to unknown provider: {}'
                        logger.warning(w.format(core_file, str(e)))

    def add_library(self, library):
        abspath = os.path.abspath(os.path.expanduser(library.location))
        _library = self._lm.get_library(abspath, "location")
        if _library:
            _s = "Not adding library {} ({}). Library {} already registered for this location"
            logger.warning(_s.format(library.name, abspath, _library.name))
            return

        self.load_cores(library)
        self._lm.add_library(library)

    def get_libraries(self):
        return self._lm.get_libraries()

    def get_depends(self, core, flags):
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
        return {str(x.name): x for x in self.db.find()}

    def get_core(self, name):
        c = self.db.find(name)
        c.name.relation = "=="
        return c

    def get_generators(self):
        generators = {}
        for core in self.db.find():
            if hasattr(core, "get_generators"):
                _generators = core.get_generators({})
                if _generators:
                    generators[str(core.name)] = _generators
        return generators
