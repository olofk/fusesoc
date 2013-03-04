import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.core import Core
from orpsoc.coremanager import CoreManager
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

        self.cores = self.config.get('main', 'cores').split()

        #Add system-specific core
        self.cores += [self.name]

        self.simulators = self.config.get('main','simulators').split()

        if self.config.has_option('main', 'backend'):
            self.backend_name = self.config.get('main','backend')
            if self.backend_name and self.config.has_section(self.backend_name):
                self.backend = dict(self.config.items(self.backend_name))

        logger.debug('self.cores=' + str(self.cores))
        logger.debug('__init__() -Done-')

    def get_cores(self):
        logger.debug('get_cores() *Entered*')
        return self.cores

    def info(self):
        logger.debug('info() *Entered*')
        # TODO: finish and make look better
        print "SYSTEM INFO"
        print "Name                  :", self.name
        print "Cores                 :",
        n = 0 
        for core_name in self.cores:
          print ' '*n + core_name
          n = 24
        print "Simulators            :",
        n = 0
        for simulator_name in self.simulators:
          print ' '*n + simulator_name
          n = 24
        #print "Backend               :", self.backend
        #print "Backend name          :", self.backend['name']
        print "Backend name          :", self.backend_name
        if self.backend_name:
            print "        family        :", self.backend['family']
            print "        tcl_files     :", self.backend['tcl_files']
            print "        sdc_files     :", self.backend['sdc_files']
            print "        simulators    :", self.backend['simulators']
            print "        cores         :", self.backend['cores']
            print "        device        :", self.backend['device']
            print "        include files :", self.backend['include_files']
            print "        src files     :", self.backend['src_files']
            print "        tb files      :", self.backend['tb_files']
            print "        backend       :", self.backend['backend']
 
