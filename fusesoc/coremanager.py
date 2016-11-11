import collections
import logging
import os

from okonomiyaki.versions import EnpkgVersion

from simplesat.constraints import PrettyPackageStringParser, Requirement
from simplesat.dependency_solver import DependencySolver
from simplesat.errors import NoPackageFound, SatisfiabilityError
from simplesat.package import PackageMetadata
from simplesat.pool import Pool
from simplesat.repository import Repository
from simplesat.request import Request

from fusesoc.config import Config
from fusesoc.core import Core
from fusesoc.utils import pr_warn

logger = logging.getLogger(__name__)

class DependencyError(Exception):
    def __init__(self, value):
        self.value = value
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
            found = self._cores[str(vlnv)]
        else:
            found = list(self._cores.values())
        return found

    #FIXME: Fails to request !highest version (wb_sdram_ctrl-0 gets wb_sdram_ctrl-0-r2)
    def solve(self, top_core, tool):
        repo = Repository()
        for core in self._cores.values():
            package_str = "{} {}-{}".format(self._package_name(core.name),
                                            core.name.version,
                                            core.name.revision)
            _depends = core.depend
            try:
                _depends += getattr(core, tool).depend
            except (AttributeError, KeyError):
                pass

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
        solver = DependencySolver(pool, repo, installed_repository)

        try:
            transaction = solver.solve(request)
        except SatisfiabilityError as e:
            msg = "UNSATISFIABLE: {}"
            raise RuntimeError(msg.format(e.unsat.to_string(pool)))
        except NoPackageFound as e:
            raise DependencyError(top_core.name)

        return [op.package.core for op in transaction.operations]

class CoreManager(object):
    _instance = None
    _cores_root = []
    tool = ''
    db = CoreDB()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CoreManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def load_core(self, file):
        if os.path.exists(file):
            try:
                core = Core(file)
                self.db.add(core)
            except SyntaxError as e:
                w = "Failed to parse " + file + ": " + e.msg
                pr_warn(w)
                logger.warning(w)
            except ImportError as e:
                pr_warn('Failed to register "{}" due to unknown provider: {}'.format(file, str(e)))
        
    def load_cores(self, path):
        if path:
            logger.debug("Checking for cores in " + path)
        if os.path.isdir(path) == False:
            raise IOError(path + " is not a directory")
        for root, dirs, files in os.walk(path, followlinks=True):
            for f in files:
                if f.endswith('.core'):
                    d = os.path.basename(root)
                    self.load_core(os.path.join(root, f))
                    del dirs[:]

    def add_cores_root(self, path):
        if path is None:
            return
        elif not isinstance(path, list):
            path = [path]
        for p in path:
            if not p:
                # skip empty entries
                continue
            abspath = os.path.abspath(os.path.expanduser(p))
            if not abspath in self._cores_root:
                self.load_cores(os.path.expanduser(p))
                self._cores_root += [abspath]

    def get_cores_root(self):
        return self._cores_root

    def get_depends(self, core):
        return self.db.solve(core, self.tool)

    def get_cores(self):
        return {str(x.name) : x for x in self.db.find()}

    def get_core(self, name):
        c = self.db.solve(name, "")[-1]
        c.name.relation = "=="
        return c

    def get_systems(self):
        return {str(x.name) : x for x in self.db.find() if x.backend}
