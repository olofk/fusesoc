import logging
import os.path

from fusesoc.edatool import EdaTool

logger = logging.getLogger(__name__)

class Backend(EdaTool):

    def configure(self, args):
        self.parse_args(args, 'build', ['vlogparam', 'vlogdefine'])
