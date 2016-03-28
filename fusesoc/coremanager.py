import collections
import logging
import os

from fusesoc.config import Config
from fusesoc.core import Core
from fusesoc.utils import pr_warn

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

    def load_core(self, file):
        if os.path.exists(file):
            try:
                core = Core(file)
                self._cores[core.name] = core
                logger.debug("Adding core " + file)
            except SyntaxError as e:
                w = "Failed to parse " + file + ": " + e.msg
                pr_warn(w)
                logger.warning(w)
            except ImportError as e:
                pr_warn('Failed to register core "{}"  due to unknown provider: {}'.format(name, str(e)))
        
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
            abspath = os.path.abspath(os.path.expanduser(p))
            if not abspath in self._cores_root:
                self._cores_root += [abspath]
                self.load_cores(os.path.expanduser(p))

    def get_cores_root(self):
        return self._cores_root

    def get_depends(self, core):
        try:
            depends = self._cores[core].depend
        except(KeyError):
            raise DependencyError(core)
        try:
            depends += getattr(self._cores[core], self.tool).depend
        except (AttributeError, KeyError):
            pass
        if depends:
            return list(collections.OrderedDict.fromkeys(self._get_depends(core)))
        else:
            return [core]

    def _get_depends(self, core):
        #FIXME: Check for circular dependencies
        try:
            cores = []
            try:
                cores += getattr(self._cores[core], self.tool).depend
            except (AttributeError, KeyError):
                pass
            if self._cores[core].depend:
                for c in self._cores[core].depend:
                    cores += self._get_depends(c)
            cores += [core]
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
