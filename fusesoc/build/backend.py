import logging
import os.path

from fusesoc.edatool import EdaTool
from fusesoc.utils import Launcher


logger = logging.getLogger(__name__)

class Backend(EdaTool):

    TOOL_TYPE = 'bld'

    def __init__(self, system, eda_api=None):
        super(Backend, self).__init__(system, eda_api)

        self.env['SYSTEM_ROOT'] = os.path.abspath(self.system.files_root)

    def configure(self, args):
        self.parse_args(args, 'build', ['vlogparam', 'vlogdefine'])
        super(Backend, self).configure(args)

    def build(self, args):
        if not self.system.scripts:
            return
        for script in self.system.scripts.pre_synth_scripts:
            script = os.path.abspath(os.path.join(self.system.files_root, script))
            logger.info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.work_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")

    def done(self):
        if not self.system.scripts:
            return
        for script in self.system.scripts.post_impl_scripts:
            script = os.path.abspath(os.path.join(self.system.files_root, script))
            logger.info("Running " + script);
            try:
                Launcher(script, cwd = os.path.abspath(self.work_root), env = self.env, shell=True).run()
            except RuntimeError:
                print("Error: script " + script + " failed")
