import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.core import Core
from orpsoc.config import Config
from orpsoc.verilog import Verilog
import os

class System:
    def __init__(self, system_file):
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

    def setup_cores(self):
        for core in self.cores:
            self.cores[core].setup()

    def _create_orpsoc_core(self, config, system_root):
        core = Core(name=self.name, core_root=system_root)
        if config.has_section('plusargs'):
            core.vpi = Plusargs(dict(config.items('plusargs')))
        if config.has_section('verilog'):
            core.verilog = Verilog(dict(config.items('verilog')))
        if config.has_section('vpi'):
            core.vpi = Vpi(dict(config.items('vpi')))
        

        return core
        
    def get_cores(self):
        return self.cores

    def get_src_files(self):
        return self.src_files
            #FIXME: Iterate through core RTL files and append to rtl_files
    def get_tb_files(self):
        return self.tb_files
