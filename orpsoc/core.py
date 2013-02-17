import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.config import Config
from orpsoc.plusargs import Plusargs
from orpsoc.provider import ProviderFactory
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
        self.plusargs = None
        self.provider = None
        self.verilog  = None
        self.vpi = None
        if core_file:
            config = configparser.SafeConfigParser()
            if not os.path.exists(core_file):
                print("Could not find " + core_file)
                exit(1)
            f = open(core_file)
            capi = f.readline().split('=')
            if capi[0].strip().upper() == 'CAPI':
                try:
                    self.capi = int(capi[1].strip())
                except ValueError:
                    print("Unknown CAPI version: \"" + capi[1].strip()+'" in ' + core_file)
                except IndexError:
                    raise SyntaxError("Could not find CAPI version in " + core_file)
            else:
                raise SyntaxError("Could not find CAPI version in " + core_file)
            config.readfp(f)

            if config.has_option('main', 'name'):
                self.name = config.get('main','name')
            else:
                self.name = basename.split('.core')[0]

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
                items = config.items('verilog')
                self.verilog = Verilog(dict(items))
                logger.debug('verilog.src_files=' + str(self.verilog.src_files))
                logger.debug('verilog.include_files=' + str(self.verilog.include_files))
                logger.debug('verilog.include_dirs=' + str(self.verilog.include_dirs))
            if config.has_section('vpi'):
                items = config.items('vpi')
                self.vpi = VPI(dict(items))

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
            self.provider.fetch(self.cache_dir)
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
                logger.debug("  File " + f + " doesn't exist - may it will be added as patch later?")
                print("File " + os.path.join(src_dir, f) + " doesn't exist")
                exit(1)
        logger.debug('export() -Done-')
        
    def patch(self, dst_dir):
        logger.debug('patch() *Entered*')
        logger.debug("  name=" + self.name)
        #FIXME: Use native python patch instead
        patch_root = os.path.join(Config().cores_root, self.name, 'patches')
        if os.path.exists(patch_root):
            for f in sorted(os.listdir(patch_root)):
                if os.path.isfile(os.path.join(patch_root, f)):
                    logger.debug("  applying patch file: " + os.path.join(patch_root, f) + "\n" +
                                 "                   to: " + os.path.join(dst_dir))
                    try:
                        subprocess.call(['patch','-p1', '-s',
                                         '-d', os.path.join(dst_dir),
                                         '-i', os.path.join(patch_root, f)])
                    except OSError:
                        print("Error: Failed to call external command 'patch'")
                        return False
        logger.debug('patch() -Done-')
        return True

    def info(self):
        logger.debug('info() *Entered*')
        # TODO: finish and make look better
        print "CORE INFO"
        print "Name                  :", self.name
        print "Core root             :", self.core_root
        #if core_file:
        #    print 
        #    if config.has_section('provider'):
        logger.debug('info() -Done-')


