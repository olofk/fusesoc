import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.core import Core
from orpsoc.config import Config
from orpsoc.verilog import Verilog
import os
import logging

logger = logging.getLogger(__name__)

class System:
    def __init__(self, system_file):
        logger.debug('__init__() *Entered*' +
                     '\n    system_file=' + str(system_file)
                    )
        system_root = os.path.dirname(system_file)

        self.config = configparser.SafeConfigParser()
        self.config.readfp(open(system_file))

        self.name = self.config.get('main', 'name')

        self.cores = {}
        self.cores['orpsoc'] = self._create_orpsoc_core(self.config, system_root)
        
        
        cores = self.config.get('main', 'cores').split()

        for core in cores:
            core_file = os.path.join(Config().cores_root,core,core+'.core')
            self.cores[core] = Core(core_file)

        self.simulators = self.config.get('main','simulators').split()

        if self.config.has_option('main', 'backend'):
            self.backend_name = self.config.get('main','backend')
            if self.backend_name and self.config.has_section(self.backend_name):
                self.backend = dict(self.config.items(self.backend_name))

        logger.debug('self.cores=' + str(self.cores))
        logger.debug('__init__() -Done-')

    def setup_cores(self):
        logger.debug('setup_cores() *Entered*')
        for core in self.cores:
            self.cores[core].setup()
        logger.debug('setup_cores() -Done-')

    def _create_orpsoc_core(self, config, system_root):
        logger.debug('_create_orpsoc_core() *Entered*')
        core = Core(name=self.name, core_root=system_root)
        if config.has_section('plusargs'):
            core.vpi = Plusargs(dict(config.items('plusargs')))
        if config.has_section('verilog'):
            core.verilog = Verilog(dict(config.items('verilog')))
        if config.has_section('vpi'):
            core.vpi = Vpi(dict(config.items('vpi')))
        

        return core
        
    def get_cores(self):
        logger.debug('get_cores() *Entered*')
        return self.cores

    def get_src_files(self):
        logger.debug('get_src_files() *Entered*')
        return self.src_files
            #FIXME: Iterate through core RTL files and append to rtl_files
    def get_tb_files(self):
        logger.debug('get_tb_files() *Entered*')
        return self.tb_files
