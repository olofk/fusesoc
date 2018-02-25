import logging

from fusesoc.edatool import EdaTool

logger = logging.getLogger(__name__)

class Simulator(EdaTool):

    def run(self, args):
        logger.info("Running")
        self.parse_args(args, self.argtypes)
        if 'pre_run_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['pre_run_scripts'])

    def done(self, args):
        if 'post_run_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['post_run_scripts'])
