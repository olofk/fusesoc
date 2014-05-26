import importlib
import logging
import os
import shutil
import subprocess

from fusesoc import section
from fusesoc import utils
from fusesoc.config import Config
from fusesoc.fusesocconfigparser import FusesocConfigParser
from fusesoc.plusargs import Plusargs
from fusesoc.system import System

logger = logging.getLogger(__name__)


class OptionSectionMissing(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Core:
    def __init__(self, core_file=None, name=None, core_root=None):
        if core_file:
            basename = os.path.basename(core_file)
        self.depend = []
        self.simulators = []

        self.plusargs = None
        self.provider = None
        self.system   = None

        for s in section.SECTION_MAP:
            assert(not hasattr(self, s))
            setattr(self, s, None)

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

            for s in section.load_all(config, name=self.name):
                setattr(self, s.TAG, s)

            self.pre_run_scripts  = config.get_list('scripts','pre_run_scripts')
            self.post_run_scripts = config.get_list('scripts','post_run_scripts')

            self.core_root = os.path.dirname(core_file)

            if config.has_section('plusargs'):
                self.plusargs = Plusargs(dict(config.items('plusargs')))
            if config.has_section('provider'):
                self.cache_dir = os.path.join(Config().cache_root, self.name)
                self.files_root = self.cache_dir
                items    = dict(config.items('provider'))

                provider_name = items.get('name')
                if provider_name is None:
                    raise RuntimeError('Missing "name" in section [provider]')
                try:
                    provider_module = importlib.import_module(
                            'fusesoc.provider.%s' % provider_name)
                    self.provider = provider_module.PROVIDER_CLASS(items)
                except ImportError:
                    raise RuntimeError(
                            'Unknown provider "%s" in section [provider]' %
                            provider_name)
            else:
                self.files_root = self.core_root

            system_file = os.path.join(self.core_root, self.name+'.system')
            if os.path.exists(system_file):
                self.system = System(system_file)
        else:
            self.name = name

            self.core_root = core_root
            self.cache_root = core_root
            self.files_root = core_root

            self.provider = None


    def cache_status(self):
        if self.provider:
            return self.provider.status(self.cache_dir)
        else:
            return 'local'

    def setup(self):
        if self.provider:
            if self.provider.fetch(self.cache_dir, self.name):
                self.patch(self.cache_dir)

    def export(self, dst_dir):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        src_dir = self.files_root

        #FIXME: Separate tb_files to an own directory tree (src/tb/core_name ?)
        src_files = []
        if self.verilog:
            src_files += self.verilog.export()
        if self.vpi:
            src_files += self.vpi.export()
        if self.verilator:
            src_files += self.verilator.export()
        if self.vhdl:
            src_files += self.vhdl.export()

        dirs = list(set(map(os.path.dirname,src_files)))
        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in src_files:
            if(os.path.exists(os.path.join(src_dir, f))):
                shutil.copyfile(os.path.join(src_dir, f), 
                                os.path.join(dst_dir, f))
            else:
                utils.pr_warn('File %s does not exist' %
                        os.path.join(src_dir, f))

    def patch(self, dst_dir):
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
        return True

    def info(self):

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


