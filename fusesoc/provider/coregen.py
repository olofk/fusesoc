from fusesoc.utils import Launcher
import os
import shutil
import logging

logger = logging.getLogger(__name__)

class Coregen(object):
    def __init__(self, config, core_root, cache_root):
        self.core_root    = core_root
        self.files_root   = cache_root
        self.script_file  = config.get('script_file')
        self.project_file = config.get('project_file')
        self.extra_files  = config.get('extra_files')

    def fetch(self):
        status = self.status()
        if status != 'downloaded':
            self._checkout()
            return True
        return False

    def _checkout(self):
        logger.info("Using Coregen to generate project " + self.project_file)
        if not os.path.isdir(self.files_root):
            os.mkdir(self.files_root)
        src_files = [self.script_file, self.project_file]
        if self.extra_files:
            src_files += self.extra_files.split()

        for f in src_files:
            f_src = os.path.join(self.core_root, f)
            f_dst = os.path.join(self.files_root, f)
            if os.path.exists(f_src):
                d_dst = os.path.dirname(f_dst)
                if not os.path.exists(d_dst):
                    os.makedirs(d_dst)
                shutil.copyfile(f_src, f_dst)
            else:
                logger.error('Cannot find file %s' % f_src)
        args = ['-r',
                '-b', self.script_file,
                '-p', self.project_file]
                #'-intstyle', 'silent']
        Launcher('coregen', args, cwd=self.files_root).run()

    def status(self):
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'

PROVIDER_CLASS = Coregen
