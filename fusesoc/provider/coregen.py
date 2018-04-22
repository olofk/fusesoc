import logging
import os
import shutil
from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher

logger = logging.getLogger(__name__)

class Coregen(Provider):

    def _checkout(self, local_dir):
        script_file  = self.config.get('script_file')
        project_file = self.config.get('project_file')
        extra_files  = self.config.get('extra_files')
        logger.info("Using Coregen to generate project " + project_file)
        if not os.path.isdir(local_dir):
            os.makedirs(local_dir)
        src_files = [script_file, project_file]
        if extra_files:
            src_files += extra_files.split()

        for f in src_files:
            f_src = os.path.join(self.core_root, f)
            f_dst = os.path.join(local_dir, f)
            if os.path.exists(f_src):
                d_dst = os.path.dirname(f_dst)
                if not os.path.exists(d_dst):
                    os.makedirs(d_dst)
                shutil.copyfile(f_src, f_dst)
            else:
                logger.error('Cannot find file %s' % f_src)
        args = ['-r',
                '-b', script_file,
                '-p', project_file]
        Launcher('coregen', args, cwd=local_dir).run()
