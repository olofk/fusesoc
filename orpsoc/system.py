import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.config import Config
import os
import logging

logger = logging.getLogger(__name__)

class System:
    def __init__(self, system_file):
        logger.debug('__init__() *Entered*' +
                     '\n    system_file=' + str(system_file)
                    )
        self.simulators = []
        self.backend_name = None

        system_root = os.path.dirname(system_file)

        self.config = configparser.SafeConfigParser()
        self.config.readfp(open(system_file))

        self.name = os.path.basename(system_file).split('.')[0]

        if self.config.has_option('main','simulators'):
            self.simulators = self.config.get('main','simulators').split()
        
        if self.config.has_option('main', 'backend'):
            self.backend_name = self.config.get('main','backend')
            if self.backend_name and self.config.has_section(self.backend_name):
                self.backend = dict(self.config.items(self.backend_name))

        logger.debug('__init__() -Done-')

    def info(self):
        logger.debug('info() *Entered*')
        # TODO: finish and make look better
        print("SYSTEM INFO")
        print("Name                  :" + self.name)
        print("Simulators            :")
        n = 0
        for simulator_name in self.simulators:
          print(' '*n + simulator_name)
          n = 24
        #print "Backend               :", self.backend
        #print "Backend name          :", self.backend['name']
        if self.backend_name:
            print("Backend name          :" + self.backend_name)
            print("        family        :"+ self.backend['family'])
            print("        tcl_files     :"+ self.backend['tcl_files'])
            print("        sdc_files     :"+ self.backend['sdc_files'])
            print("        simulators    :"+ self.backend['simulators'])
            print("        cores         :"+ self.backend['cores'])
            print("        device        :"+ self.backend['device'])
            print("        include files :"+ self.backend['include_files'])
            print("        src files     :"+ self.backend['src_files'])
            print("        tb files      :"+ self.backend['tb_files'])
            print("        backend       :"+ self.backend['backend'])
 
