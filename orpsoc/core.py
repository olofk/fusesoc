from orpsoc.orpsocconfigparser import OrpsocConfigParser
from orpsoc.config import Config
from orpsoc.plusargs import Plusargs
from orpsoc.provider import ProviderFactory
from orpsoc.system import System
from orpsoc.vpi import VPI
from orpsoc.verilog import Verilog
import os
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

class Core:
    def __init__(self, core_file=None, name=None, core_root=None):
        logger.debug('__init__() *Entered*' +
                     '\n    core_file=' + str(core_file) +
                     '\n    name=' + str(name) + 
                     '\n    core_root=' + str(core_root)
                    )
        if core_file:
            basename = os.path.basename(core_file)
        self.depend = []
        self.simulators = []

        self.plusargs = None
        self.provider = None
        self.system   = None
        self.verilog  = None
        self.vpi = None
        if core_file:
            config = OrpsocConfigParser(core_file)

            if config.has_option('main', 'name'):
                self.name = config.get('main','name')
            else:
                self.name = basename.split('.core')[0]

            self.depend     = config.get_list('main', 'depend')
            self.simulators = config.get_list('main', 'simulators')

            #FIXME : Make simulators part of the core object
            self.simulator        = config.get_section('simulator')
            self.iverilog_options = config.get_list('icarus','iverilog_options')
            self.vlog_options     = config.get_list('modelsim','vlog_options')
            self.vsim_options     = config.get_list('modelsim','vsim_options')
            self.verilator = config.get_section('verilator')

            logger.debug('name=' + str(self.name))
            self.core_root = os.path.dirname(core_file)

            if config.has_section('plusargs'):
                self.plusargs = Plusargs(dict(config.items('plusargs')))
            if config.has_section('provider'):
                self.cache_dir = os.path.join(Config().cache_root, self.name)
                self.files_root = self.cache_dir
                items    = config.items('provider')
                self.provider = ProviderFactory(dict(items))
            else:
                self.files_root = self.core_root

            if config.has_section('verilog'):
                self.verilog = Verilog()
                items = config.items('verilog')
                self.verilog.load_items((dict(items)))
                logger.debug('verilog.src_files=' + str(self.verilog.src_files))
                logger.debug('verilog.include_files=' + str(self.verilog.include_files))
                logger.debug('verilog.include_dirs=' + str(self.verilog.include_dirs))
            if config.has_section('vpi'):
                items = config.items('vpi')
                self.vpi = VPI(dict(items))
            system_file = os.path.join(self.core_root, self.name+'.system')
            if os.path.exists(system_file):
                self.system = System(system_file)
        else:
            self.name = name

            self.core_root = core_root
            self.cache_root = core_root
            self.files_root = core_root

            self.provider = None
        logger.debug('__init__() -Done-')


    def cache_status(self):
        logger.debug('cache_status() *Entered*')
        if self.provider:
            return self.provider.status(self.cache_dir)
        else:
            return 'local'

    def setup(self):
        logger.debug('setup() *Entered*')
        logger.debug("  name="+self.name)
        if self.provider:
            if self.provider.fetch(self.cache_dir):
                self.patch(self.cache_dir)
        logger.debug('setup() -Done-')

    def export(self, dst_dir):
        logger.debug('export() *Entered*')
        logger.debug("  name="+self.name)
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        src_dir = self.files_root

        #FIXME: Separate tb_files to an own directory tree (src/tb/core_name ?)
        src_files = []
        if self.verilog:
            src_files += self.verilog.export()
        if self.vpi:
            src_files += self.vpi.export()

        dirs = list(set(map(os.path.dirname,src_files)))
        logger.debug("export src_files=" + str(src_files))
        logger.debug("export dirs=" + str(dirs))
        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in src_files:
            if(os.path.exists(os.path.join(src_dir, f))):
                shutil.copyfile(os.path.join(src_dir, f), 
                                os.path.join(dst_dir, f))
            else:
                print("File " + os.path.join(src_dir, f) + " doesn't exist")
        logger.debug('export() -Done-')
        
    def patch(self, dst_dir):
        logger.debug('patch() *Entered*')
        logger.debug("  name=" + self.name)
        #FIXME: Use native python patch instead
        patch_root = os.path.join(self.core_root, 'patches')
        if os.path.exists(patch_root):
            for f in sorted(os.listdir(patch_root)):
                patch_file = os.path.abspath(os.path.join(patch_root, f))
                if os.path.isfile(patch_file):
                    logger.debug("  applying patch file: " + patch_file + "\n" +
                                 "                   to: " + os.path.join(dst_dir))
                    try:
                        subprocess.call(['patch','-p1', '-s',
                                         '-d', os.path.join(dst_dir),
                                         '-i', patch_file])
                    except OSError:
                        print("Error: Failed to call external command 'patch'")
                        return False
        logger.debug('patch() -Done-')
        return True

    def info(self):
        logger.debug('info() *Entered*')
        # TODO: finish and make look better
        print("CORE INFO")
        print("Name                  :" + self.name)
        print("Core root             :" + self.core_root)
        print("Simulators            :")
        n = 0
        for simulator_name in self.simulators:
          print(' '*n + simulator_name)
          n = 24
        #if core_file:
        #    print 
        #    if config.has_section('provider'):
        logger.debug('info() -Done-')


