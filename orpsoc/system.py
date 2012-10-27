import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.core import Core
from orpsoc.config import Config

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

        system_config = configparser.SafeConfigParser(DEFAULT_VALUES)
        system_config.readfp(open(system_file))

        self.name = system_config.get('main', 'name')

        self.cores = {}
        self.cores['orpsoc'] = self._create_orpsoc_core(system_config, system_root)
        
        
        cores = system_config.get('main', 'cores').split()

        for core in cores:
            core_file = os.path.join(Config().cores_root,core,core+'.core')
            self.cores[core] = Core(core_file)

        self.simulators = system_config.get('main','simulators').split()

    def setup_cores(self):
        for core in self.cores:
            self.cores[core].setup()

    def _create_orpsoc_core(self, system_config, system_root):
        core = Core(name=self.name, core_root=system_root)
        
        core.rtl_files     = system_config.get('main', 'rtl_files').split()
        core.include_files = system_config.get('main', 'include_files').split()
        core.include_dirs  = list(set(map(os.path.dirname, core.include_files)))
        core.tb_files      = system_config.get('main', 'tb_files').split()

        return core
        
    def get_cores(self):
        return self.cores

    def get_rtl_files(self):
        return self.rtl_files
            #FIXME: Iterate through core RTL files and append to rtl_files
    def get_tb_files(self):
        return self.tb_files
