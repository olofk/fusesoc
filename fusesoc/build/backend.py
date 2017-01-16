import logging
import os.path
import shutil

from fusesoc.edatool import EdaTool
from fusesoc.utils import Launcher, pr_info, pr_warn


logger = logging.getLogger(__name__)

class Backend(EdaTool):

    TOOL_TYPE = 'bld'

    def __init__(self, system, export):
        super(Backend, self).__init__(system, export)

        self.backend = self.system.backend
        self.env['SYSTEM_ROOT'] = os.path.abspath(self.system.files_root)

    def configure(self, args):
        self.parse_args(args, 'build', ['vlogparam', 'vlogdefine'])
        super(Backend, self).configure(args)

    def build(self, args):
        if not self.system.scripts:
            return
        for script in self.system.scripts.pre_synth_scripts:
            script = os.path.abspath(os.path.join(self.system.files_root, script))
            pr_info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.work_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")

    def done(self):
        if not self.system.scripts:
            return
        for script in self.system.scripts.post_impl_scripts:
            script = os.path.abspath(os.path.join(self.system.files_root, script))
            pr_info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.work_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")
