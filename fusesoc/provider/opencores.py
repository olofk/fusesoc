from fusesoc.utils import Launcher, pr_info, pr_warn

import os.path
import logging

logger = logging.getLogger(__name__)

REPO_PATH = 'http://opencores.org/ocsvn/{}/{}/{}'

class ProviderOpenCores(object):
    def __init__(self, core_name, config, core_root, cache_root):
        self.repo_name = config.get('repo_name')
        self.repo_path = REPO_PATH.format(self.repo_name,
                                          self.repo_name,
                                          config.get('repo_root'))
        self.revision_number  = config.get('revision')
        self.files_root = cache_root

    def fetch(self):
        status = self.status()

        if status == 'empty':
            try:
                self._checkout(self.files_root)
                return True
            except RuntimeError:
                raise
        elif status == 'modified':
            self.clean_cache()
            try:
                self._checkout(self.files_root)
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

    def status(self):
        #FIXME: Check if repo is modified, or is an SVN repo at all, etc..
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'

    def _checkout(self, local_dir):
        pr_info("Downloading " + self.repo_name + " from OpenCores")

        Launcher('svn', ['co', '-q', '--no-auth-cache',
                         '-r', self.revision_number,
                         '--username', 'orpsoc',
                         '--password', 'orpsoc',
                         self.repo_path,
                         local_dir]).run()


    def _update(self):
        pass

PROVIDER_CLASS = ProviderOpenCores
