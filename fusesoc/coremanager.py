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

    #simplesat doesn't allow ':', '-' or leading '_'
    def _package_name(self, vlnv):
        _name = "{}_{}_{}".format(vlnv.vendor,
                                  vlnv.library,
                                  vlnv.name).lstrip("_")
        return _name.replace('-','__')

    def _package_version(self, vlnv):
        return "{}-{}".format(vlnv.version,
                              vlnv.revision)

    def _parse_depend(self, depends):
        #FIXME: Handle conflicts
        deps = []
        _s = "{} {} {}"
        for d in depends:
            deps.append(_s.format(self._package_name(d),
                                  d.relation,
                                  self._package_version(d)))
        return ", ".join(deps)

    def add(self, core):
        name = str(core.name)
        logger.debug("Adding core " + name)
        if name in self._cores:
            _s = "Replacing {} in {} with the version found in {}"
            logger.debug(_s.format(name,
                                   self._cores[name].core_root,
                                   core.core_root))
        self._cores[name] = core

    def find(self, vlnv=None):
        if vlnv:
            found = self._solve(vlnv, only_matching_vlnv=True)[-1]
        else:
            found = list(self._cores.values())
        return found

    def solve(self, top_core, flags):
        return self._solve(top_core, flags)

    def _solve(self, top_core, flags={}, only_matching_vlnv=False):
        def eq_vln(this, that):
            return \
                this.vendor  == that.vendor and \
                this.library == that.library and \
                this.name    == that.name

        repo = Repository()
        _flags = flags.copy()
        for core in self._cores.values():
            if only_matching_vlnv:
                if not eq_vln(core.name, top_core):
                    continue

            package_str = "{} {}-{}".format(self._package_name(core.name),
                                            core.name.version,
                                            core.name.revision)
            if not only_matching_vlnv:
                _flags['is_toplevel'] = (core.name == top_core)
                _depends = core.get_depends(_flags)
                if _depends:
                    _s = "; depends ( {} )"
                    package_str += _s.format(self._parse_depend(_depends))
            parser = PrettyPackageStringParser(EnpkgVersion.from_string)

            package = parser.parse_to_package(package_str)
            package.core = core

            repo.add_package(package)

        request = Request()
        _top_dep = "{} {} {}".format(self._package_name(top_core),
                                     top_core.relation,
                                     self._package_version(top_core))
        requirement = Requirement._from_string(_top_dep)
        request.install(requirement)
        installed_repository = Repository()
        pool = Pool([repo])
        pool.add_repository(installed_repository)
        solver = DependencySolver(pool, [repo], installed_repository)

        try:
            transaction = solver.solve(request)
        except SatisfiabilityError as e:
            raise DependencyError(top_core.name,
                                  msg=e.unsat.to_string(pool))
        except NoPackageFound as e:
            raise DependencyError(top_core.name)

        return [op.package.core for op in transaction.operations]

class CoreManager(object):

    def __init__(self, config):
        self.config = config
        self._cores_root = []
        self.db = CoreDB()

    def load_cores(self, path):
        if os.path.isdir(path) == False:
            raise IOError(path + " is not a directory")
        logger.debug("Checking for cores in " + path)
        for root, dirs, files in os.walk(path, followlinks=True):
            if 'FUSESOC_IGNORE' in files:
                del dirs[:]
                continue
            for f in files:
                if f.endswith('.core'):
                    core_file = os.path.join(root, f)
                    try:
                        core = Core(core_file, self.config.cache_root, self.config.build_root)
                        self.db.add(core)
                    except SyntaxError as e:
                        w = "Parse error. Ignoring file " + core_file + ": " + e.msg
                        logger.warning(w)
                    except ImportError as e:
                        w = 'Failed to register "{}" due to unknown provider: {}'
                        logger.warning(w.format(core_file, str(e)))

    def add_cores_root(self, path):
        if not path:
            return

        abspath = os.path.abspath(os.path.expanduser(path))
        if abspath in self._cores_root:
            return

        self.load_cores(os.path.expanduser(path))
        self._cores_root += [abspath]

    def get_cores_root(self):
        return self._cores_root

    def get_depends(self, core, flags):
        logger.debug("Calculating dependencies for {}{} with flags {}".format(core.relation,str(core), str(flags)))
        resolved_core = self.db.find(core)
        deps = self.db.solve(resolved_core.name, flags)
        logger.debug(" Resolved core to {}".format(str(resolved_core.name)))
        logger.debug(" with dependencies " + ', '.join([str(c.name) for c in deps]))
        return deps

    def get_cores(self):
        return {str(x.name) : x for x in self.db.find()}

    def get_core(self, name):
        c = self.db.find(name)
        c.name.relation = "=="
        return c

    def get_generators(self):
        generators = {}
        for core in self.db.find():
            if hasattr(core, 'get_generators'):
                _generators = core.get_generators({})
                if _generators:
                    generators[str(core.name)] = _generators
        return generators
