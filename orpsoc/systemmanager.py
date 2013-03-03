import logging
import os

from orpsoc.config import Config
from orpsoc.system import System

logger = logging.getLogger(__name__)

class SystemManager(object):
    _instance = None
    _systems = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SystemManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.add_systems_root(Config().systems_root)

    def load_systems(self, path):
        if path:
            logger.debug("Checking for systems in " + path)
        for d in os.listdir(path):
            f = os.path.join(path, d, d+'.system')
            if os.path.exists(f):
                try:
                    self._systems[d] = System(f)
                except SyntaxError:
                    pass

    def add_systems_root(self, path):
        if path is None:
            return
        elif isinstance(path, list):
            for p in path:
                self.load_systems(p)
        else:
            self.load_systems(path)

    def get_systems(self):
        return self._systems

    def get_system(self, name):
        if name in self._systems:
            return self._systems[name]
        else:
            return None
