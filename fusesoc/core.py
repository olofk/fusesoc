from fusesoc.fusesocconfigparser import FusesocConfigParser
from fusesoc.config import Config
from fusesoc.plusargs import Plusargs
from fusesoc.provider import ProviderFactory
from fusesoc.system import System
from fusesoc.vpi import VPI
from fusesoc.verilog import Verilog
from fusesoc.section import Section
from fusesoc.utils import pr_warn
import os
import shutil
import subprocess
import logging

logger = logging.getLogger(__name__)

class OptionSectionMissing(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

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
            config = FusesocConfigParser(core_file)

            if config.has_option('main', 'name'):
                self.name = config.get('main','name')
            else:
                self.name = basename.split('.core')[0]

            self.depend     = config.get_list('main', 'depend')
            self.simulators = config.get_list('main', 'simulators')

            #FIXME : Make simulators part of the core object
            self.simulator        = config.get_section('simulator')
            for name in ['icarus', 'modelsim', 'verilator']:
                items = config.get_section(name)
                section = Section.factory(name, items) if items else None
                setattr(self, name, section)
            self.pre_run_scripts  = config.get_list('scripts','pre_run_scripts')
            self.post_run_scripts = config.get_list('scripts','post_run_scripts')

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
            if self.provider.fetch(self.cache_dir, self.name):
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
                pr_warn("File " + os.path.join(src_dir, f) + " doesn't exist")
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

        show_list = lambda l: "\n                        ".join(l)
        show_dict = lambda d: show_list(["%s: %s" % (k, d[k]) for k in d.keys()])

        print("CORE INFO")
        print("Name:                   " + self.name)
        print("Core root:              " + self.core_root)
        if self.simulators:
            print("Simulators:             " + show_list(self.simulators))
        if self.plusargs: 
            print("\nPlusargs:               " + show_dict(self.plusargs.items))
        if self.depend:
            print("\nCores:                  " + show_list(self.depend))
        if self.verilog.include_dirs:
            print("\nInclude dirs:           " + show_list(self.verilog.include_dirs))
        if self.verilog.include_files:
            print("\nInclude files:          " + show_list(self.verilog.include_files))
        if self.verilog.src_files:
            print("\nSrc files:              " + show_list(self.verilog.src_files))
        if self.verilog.tb_src_files:
            print("\nTestbench files:        " + show_list(self.verilog.tb_src_files))
        if self.verilog.tb_private_src_files:
            print("\nPrivate Testbench files:" + show_list(self.verilog.tb_private_src_files))
        if self.verilog.tb_include_files:
            print("\nTestbench include files:" + show_list(self.verilog.tb_include_files))
        if self.verilog.tb_include_dirs:
            print("\nTestbench include dirs: " + show_list(self.verilog.tb_include_dirs))
        logger.debug('info() -Done-')


