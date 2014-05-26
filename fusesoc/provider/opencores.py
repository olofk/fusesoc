from fusesoc.utils import Launcher, pr_info, pr_warn

import os.path
import logging

logger = logging.getLogger(__name__)

class ProviderOpenCores(object):
    def __init__(self, config):
        self.repo_path = 'http://opencores.org/ocsvn/' + \
            config.get('repo_name') + '/' + config.get('repo_name') + '/' + \
            config.get('repo_root')
        self.revision_number  = config.get('revision')

    def fetch(self, local_dir, core_name):
        status = self.status(local_dir)

        if status == 'empty':
            try:
                self._checkout(local_dir)
                return True
            except RuntimeError:
                raise
        elif status == 'modified':
            self.clean_cache()
            try:
                self._checkout(local_dir)
                return True
            except RuntimeError:
                raise
        elif status == 'outofdate':
            self._update()
            return True
        elif status == 'downloaded':
            return False
        else:
            pr_warn("Provider status is: '" + status + "'. This shouldn't happen")
            return False

    def status(self, local_dir):
        #FIXME: Check if repo is modified, or is an SVN repo at all, etc..
        if not os.path.isdir(local_dir):
            return 'empty'
        else:
            return 'downloaded'
        
    def _checkout(self, local_dir):
        pr_info("Checking out " + self.repo_path + " revision " + self.revision_number + " to " + local_dir)

        Launcher('svn', ['co', '-q', '--no-auth-cache',
                         '-r', self.revision_number,
                         '--username', 'orpsoc',
                         '--password', 'orpsoc',
                         self.repo_path,
                         local_dir]).run()


    def _update(self):
        pass

PROVIDER_CLASS = ProviderOpenCores
