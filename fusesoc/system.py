from fusesoc import section
from fusesoc.fusesocconfigparser import FusesocConfigParser
from fusesoc.config import Config
import os
import logging

logger = logging.getLogger(__name__)

class System:
    def __init__(self, system_file):
        self.backend_name = None

        self.system_root = os.path.dirname(system_file)
        self.config = FusesocConfigParser(system_file)


        self.pre_build_scripts  = self.config.get_list('scripts','pre_build_scripts')
        self.post_build_scripts = self.config.get_list('scripts','post_build_scripts')

        if self.config.has_option('main', 'backend'):
            self.backend_name = self.config.get('main','backend')
            self.backend = section.load_section(self.config, self.backend_name,
                                                file_name=system_file)


    def info(self):
        print("\nSYSTEM INFO")
        print(self.backend)
