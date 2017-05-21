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
