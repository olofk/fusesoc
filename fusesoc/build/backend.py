import logging
import os.path

from fusesoc.edatool import EdaTool

logger = logging.getLogger(__name__)

class Backend(EdaTool):

    TOOL_TYPE = 'bld'

    def configure(self, args):
        self.parse_args(args, 'build', ['vlogparam', 'vlogdefine'])
        super(Backend, self).configure(args)

    def done(self):
        if 'post_build_scripts' in self.fusesoc_options:
            self._run_scripts(self.fusesoc_options['post_build_scripts'])
