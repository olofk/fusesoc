import logging

from fusesoc.edatool import EdaTool

logger = logging.getLogger(__name__)

class Simulator(EdaTool):

    def configure(self, args, skip_params = False):
        if not skip_params:
            self.parse_args(args, 'sim', ['plusarg', 'vlogdefine', 'vlogparam', 'cmdlinearg'])

    def run(self, args):
        self.parse_args(args, 'sim', ['plusarg', 'vlogdefine', 'vlogparam', 'cmdlinearg'])
        if 'pre_run_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['pre_run_scripts'])

    def done(self, args):
        if 'post_run_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['post_run_scripts'])
