import os.path
import shutil
import subprocess

from orpsoc.config import Config
from orpsoc.coremanager import CoreManager
from orpsoc import utils
import logging

logger = logging.getLogger(__name__)

class Backend(object):

    def __init__(self, system):
        logger.debug('__init__() *Entered*')
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.systems_root = config.systems_root

        self.src_root = os.path.join(self.build_root, 'src')

        self.include_dirs = []
        self.src_files = []
        self.cm = CoreManager()

        self.cores = self.cm.get_depends(self.system.name)
        for core_name in self.cores:
            logger.debug('core_name=' + core_name)
            core = self.cm.get_core(core_name)
            if core.verilog:
                if core.verilog.include_dirs:
                    logger.debug('core.include_dirs=' + str(core.verilog.include_dirs))
                else:
                    logger.debug('core.include_dirs=None')
                self.include_dirs += [os.path.join(self.src_root, core_name, d) for d in core.verilog.include_dirs]
                self.src_files    += [os.path.join(self.src_root, core_name, f) for f in core.verilog.src_files]
        logger.debug('__init__() -Done-')

    def configure(self):
        logger.debug('configure() *Entered*')
        if os.path.exists(self.work_root): 
            shutil.rmtree(self.work_root)
        os.makedirs(self.work_root)
        cm = CoreManager()
        for name in self.cores:
            print("Preparing " + name)
            core = cm.get_core(name)
            dst_dir = os.path.join(Config().build_root, self.system.name, 'src', name)
            core.setup()
            core.export(dst_dir)
        logger.debug('configure() -Done-')

    def build(self):
        pass

