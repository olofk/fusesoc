import collections
import logging
import os

from fusesoc.config import Config
from fusesoc.core import Core

logger = logging.getLogger(__name__)

class DependencyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class CoreManager(object):
    _instance = None
    _cores = {}
    _cores_root = []
    tool = ''

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CoreManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.add_cores_root(Config().cores_root)
        self.add_cores_root(Config().systems_root)

    def load_core(self, name, file):
        if os.path.exists(file):
            try:
                self._cores[name] = Core(file)
                logger.debug("Adding core " + file)
            except SyntaxError as e:
                w = "Warning: Failed to parse " + file + ": " + e.msg
                print(w)
                logger.warning(w)
        
    def load_cores(self, path):
        if path:
            logger.debug("Checking for cores in " + path)
        if os.path.isdir(path) == False:
            raise IOError(path + " is not a directory")
        for d in os.listdir(path):
            f = os.path.join(path, d, d+'.core')
            if os.path.isfile(f) == False:
                core_dir = os.path.join(path, d)
                for core_subdir in os.listdir(core_dir):
                    subcore = os.path.join(core_dir, core_subdir, core_subdir+'.core')
                    self.load_core(core_subdir, subcore)
            else:
                self.load_core(d, f)

    def add_cores_root(self, path):
        if path is None:
            return
        elif isinstance(path, list):
            for p in path:
                abspath = os.path.abspath(p)
                if not abspath in self._cores_root:
                    self._cores_root += [abspath]
                    self.load_cores(p)
        else:
            abspath = os.path.abspath(path)
            if not abspath in self._cores_root:
                self._cores_root += [abspath]
                self.load_cores(path)

    def get_cores_root(self):
        return self._cores_root

    def get_depends(self, core):
        depends = self._cores[core].depend
        try:
            depends += getattr(self._cores[core], self.tool).depend
        except (AttributeError, KeyError):
            pass
        if depends:
            return list(set(self._get_depends(core)))
        else:
            return [core]

    def _get_depends(self, core):
        #FIXME: Check for circular dependencies
        try:
            cores = [core]
            try:
                cores += getattr(self._cores[core], self.tool).depend
            except (AttributeError, KeyError):
                pass
            if self._cores[core].depend:
                for c in self._cores[core].depend:
                    cores += self._get_depends(c)
            return cores
        except(KeyError):
            raise DependencyError(core)

    def get_cores(self):
        return self._cores

    def get_core(self, name):
        if name in self._cores:
            return self._cores[name]
        else:
            return None

    def get_property(self, core, attr, recursive=True):
        retval = collections.OrderedDict()

        if recursive:
            for c in self._cores[core].depend:
                if not c in retval:
                    retval.update(self.get_property(c, attr))
        try:
            retval[core] = getattr(self._cores[core], attr)
        except AttributeError:
            pass
        return retval

    def get_systems(self):
        systems = {}
        for name, core in self._cores.items():
            if core.system:
                systems[name] = core
        return systems
