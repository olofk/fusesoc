import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.core import Core
from orpsoc.config import Config
from orpsoc.verilog import Verilog
import os

DEFAULT_VALUES = {'name'          : '',
                  'cores'         : '',
                  'simulators'    : '',
                  'backend'       : '',
                  'include_files' : '',
                  'rtl_files'     : '',
                  'tb_files'      : ''}

class System:
    def __init__(self, system_file):
        system_root = os.path.dirname(system_file)

        self.config = configparser.SafeConfigParser(DEFAULT_VALUES)
        self.config.readfp(open(system_file))

        self.name = self.config.get('main', 'name')

        self.cores = {}
        self.cores['orpsoc'] = self._create_orpsoc_core(self.config, system_root)
        
        
        cores = self.config.get('main', 'cores').split()

        for core in cores:
            core_file = os.path.join(Config().cores_root,core,core+'.core')
            self.cores[core] = Core(core_file)

        self.simulators = self.config.get('main','simulators').split()

        self.backend_name = self.config.get('main','backend')
        if self.backend_name and self.config.has_section(self.backend_name):
            self.backend = dict(self.config.items(self.backend_name))

    def setup_cores(self):
        for core in self.cores:
            self.cores[core].setup()

    def _create_orpsoc_core(self, config, system_root):
        core = Core(name=self.name, core_root=system_root)

        items = {}
        if config.has_option('main','rtl_files'):
            items['src_files'] = config.get('main', 'rtl_files')
        if config.has_option('main','include_files'):
            items['include_files'] = config.get('main', 'include_files')
        if config.has_option('main','tb_files'):
            items['tb_src_files'] = config.get('main', 'tb_files')

        core.verilog = Verilog(items)
        return core
        
    def get_cores(self):
        return self.cores

    def get_rtl_files(self):
        return self.rtl_files
            #FIXME: Iterate through core RTL files and append to rtl_files
    def get_tb_files(self):
        return self.tb_files
