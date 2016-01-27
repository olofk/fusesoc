import os

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager

class EdaTool(object):

    def __init__(self, system):
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.src_root = os.path.join(self.build_root, 'src')

        self.cm = CoreManager()
        self.cores = self.cm.get_depends(self.system.name)

        self.env = os.environ.copy()
        self.env['BUILD_ROOT'] = os.path.abspath(self.build_root)
