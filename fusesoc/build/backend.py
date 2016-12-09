import logging
import os.path
import shutil

from fusesoc.edatool import EdaTool
from fusesoc.utils import Launcher, pr_info, pr_warn


logger = logging.getLogger(__name__)

class Backend(EdaTool):

    TOOL_TYPE = 'bld'

    def __init__(self, system):
        super(Backend, self).__init__(system)

        self.backend = self.system.backend
        self.env['SYSTEM_ROOT'] = os.path.abspath(self.system.files_root)
        self.env['BACKEND'] = self.TOOL_NAME

    def configure(self, args):
        self.parse_args(args, 'build', ['vlogparam', 'vlogdefine'])
        super(Backend, self).configure(args)
        self._export_backend_files()

    def _export_backend_files(self):
        src_dir = self.system.files_root
        dst_dir = os.path.join(self.src_root, self.system.sanitized_name)

        export_files = self.backend.export()
        dirs = list(set([os.path.dirname(f.name) for f in export_files]))

        for d in dirs:
            if not os.path.exists(os.path.join(dst_dir, d)):
                os.makedirs(os.path.join(dst_dir, d))

        for f in export_files:
            if(os.path.exists(os.path.join(src_dir, f.name))):
                shutil.copyfile(os.path.join(src_dir, f.name),
                                os.path.join(dst_dir, f.name))
            else:
                pr_warn("File " + os.path.join(src_dir, f.name) + " doesn't exist")

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
