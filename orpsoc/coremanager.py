import logging
import os

from orpsoc.config import Config
from orpsoc.core import Core

logger = logging.getLogger(__name__)

class CoreManager(object):
    _instance = None
    _cores = {}
    _cores_root = []

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
            except SyntaxError:
                logger.debug("Failed to parse " + file)
        
    def load_cores(self, path):
        if path:
            logger.debug("Checking for cores in " + path)
        for d in os.listdir(path):
            f = os.path.join(path, d, d+'.core')
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

    def get_depends(self, core):
        return self._get_depends(core)

    def _get_depends(self, core):
        #FIXME: Check for circular dependencies and duplicates
        if self._cores[core].depend:
            c = self._cores[core].depend
            d = map(self._get_depends, c) + [core]
            return d
        else:
            return core

    def get_cores(self):
        return self._cores

    def get_core(self, name):
        if name in self._cores:
            return self._cores[name]
        else:
            return None

    def get_systems(self):
        systems = {}
        for name, core in self._cores.items():
            if core.system:
                systems[name] = core
        return systems
