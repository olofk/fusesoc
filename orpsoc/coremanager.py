import logging
import os

from orpsoc.config import Config
from orpsoc.core import Core

logger = logging.getLogger(__name__)

class CoreManager(object):
    _instance = None
    _cores = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CoreManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.add_cores_root(Config().cores_root)

    def load_cores(self, path):
        if path:
            logger.debug("Checking for cores in " + path)
        for d in os.listdir(path):
            f = os.path.join(path, d, d+'.core')
            if os.path.exists(f):
                try:
                    self._cores[d] = Core(f)
                except SyntaxError:
                    pass

    def add_cores_root(self, path):
        if path is None:
            return
        elif isinstance(path, list):
            for p in path:
                self.load_cores(p)
        else:
            self.load_cores(path)

    def get_cores(self):
        return self._cores

    def get_core(self, name):
        if name in self._cores:
            return self._cores[name]
        else:
            return None
