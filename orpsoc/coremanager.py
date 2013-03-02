import os

from orpsoc.config import Config
from orpsoc.core import Core

class CoreManager(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(CoreManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._cores = {}
        self.load_cores(Config().cores_root)

    def load_cores(self, path):
        for d in os.listdir(path):
            f = os.path.join(path, d, d+'.core')
            if os.path.exists(f):
                try:
                    self._cores[d] = Core(f)
                except SyntaxError:
                    pass

    def add_cores_root(self, path):
        self.load_cores(path)

    def get_cores(self):
        return self._cores

    def get_core(self, name):
        return self._cores[name]
