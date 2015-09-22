import os.path
import shutil
import subprocess
import sys

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
    from urllib.error import HTTPError
else:
    import urllib
    from urllib2 import URLError
    from urllib2 import HTTPError

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager
from fusesoc.utils import Launcher, pr_info, pr_warn
from fusesoc import utils
import logging

logger = logging.getLogger(__name__)

class Backend(object):

    def __init__(self, system):
        config = Config()
        self.system = system
        self.build_root = os.path.join(config.build_root, self.system.name)
        self.system_root = system.system_root

        self.src_root = os.path.join(self.build_root, 'src')

        self.include_dirs = []
        self.src_files = []
        self.vhdl_src_files = []
        self.cm = CoreManager()

        self.env = os.environ.copy()
        self.env['SYSTEM_ROOT'] = os.path.abspath(self.system_root)
        self.env['BUILD_ROOT'] = os.path.abspath(self.build_root)
        self.env['BACKEND'] = self.TOOL_NAME

        self.cores = self.cm.get_depends(self.system.name)
        for core_name in self.cores:
            logger.debug('core_name=' + core_name)
            core = self.cm.get_core(core_name)
            if core.verilog:
                if core.verilog.include_dirs:
                    logger.debug('core.include_dirs=' + str(core.verilog.include_dirs))
                else:
                    logger.debug('core.include_dirs=None')
                self.include_dirs += [os.path.join(self.src_root, core_name, d) for d in core.verilog.include_dirs]
                self.src_files    += [os.path.join(self.src_root, core_name, f) for f in core.verilog.src_files]
            if core.vhdl:
                self.vhdl_src_files += [os.path.join(self.src_root, core_name, f) for f in core.vhdl.src_files]


    def configure(self):
        if os.path.exists(self.work_root): 
            shutil.rmtree(self.work_root)
        os.makedirs(self.work_root)
        cm = CoreManager()
        for name in self.cores:
            pr_info("Preparing " + name)
            core = cm.get_core(name)
            dst_dir = os.path.join(Config().build_root, self.system.name, 'src', name)
            try:
                core.setup()
            except URLError as e:
                raise RuntimeError("Problem while fetching '" + core.name + "': " + str(e.reason))
            except HTTPError as e:
                raise RuntimeError("Problem while fetching '" + core.name + "': " + str(e.reason))
            core.export(dst_dir)

    def build(self, args):
        for script in self.system.pre_build_scripts:
            script = os.path.abspath(os.path.join(self.system_root, script))
            pr_info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.build_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")

    def done(self):
        for script in self.system.post_build_scripts:
            script = os.path.abspath(os.path.join(self.system_root, script))
            pr_info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.build_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")
