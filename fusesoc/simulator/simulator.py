import argparse
import os
import logging

from fusesoc.edatool import EdaTool
from fusesoc.utils import run_scripts

logger = logging.getLogger(__name__)

class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [os.path.abspath(values[0])])

class Simulator(EdaTool):

    TOOL_TYPE = 'sim'

    def __init__(self, system, export):
        super(Simulator, self).__init__(system, export)

        logger.debug( "depend -->  " +str (self.cores))

        self._get_vpi_modules()

    def _get_vpi_modules(self):
        self.vpi_modules = []
        for core in self.cores:

            if core.vpi:
                vpi_module = {}
                if self.export:
                    core_root = os.path.join(self.src_root, core.sanitized_name)
                else:
                    core_root = core.files_root
                vpi_module['root']          = os.path.relpath(core_root, self.work_root)
                vpi_module['include_dirs']  = [os.path.join(vpi_module['root'], d) for d in core.vpi.include_dirs]
                vpi_module['src_files']     = [os.path.relpath(os.path.join(core_root, f.name), self.work_root) for f in core.vpi.src_files]
                vpi_module['name']          = core.sanitized_name
                vpi_module['libs']          = [l for l in core.vpi.libs]
                self.vpi_modules += [vpi_module]

    def configure(self, args, skip_params = False):
        if not skip_params:
            self.parse_args(args, 'sim', ['plusarg', 'vlogdefine', 'vlogparam', 'cmdlinearg'])
        super(Simulator, self).configure(args)

    def build(self):
        for core in self.cores:
            if core.scripts:
                run_scripts(core.scripts.pre_build_scripts,
                            core.files_root,
                            self.work_root,
                            self.env)
        return

    def run(self, args):
        self.parse_args(args, 'sim', ['plusarg', 'vlogdefine', 'vlogparam', 'cmdlinearg'])
        for core in self.cores:
            if core.scripts:
                run_scripts(core.scripts.pre_run_scripts,
                            core.core_root,
                            self.work_root,
                            self.env)

    def done(self, args):

        for core in self.cores:
            if core.scripts:
                run_scripts(core.scripts.post_run_scripts,
                            core.core_root,
                            self.work_root,
                            self.env)
