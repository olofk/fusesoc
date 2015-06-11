from fusesoc.utils import pr_info, pr_warn, Launcher
import os.path
import shutil

class Git(object):
    def __init__(self, core_name, config, core_root, cache_root):
        self.repo   = config.get('repo')
        self.cachable = True
        if 'cachable' in config:
            self.cachable = not (config.get('cachable') == 'false')
        if 'version' in config:
            self.version = config.get('version')
        else:
            self.version = None
        self.files_root = cache_root

    def clean_cache(self):
        if os.path.exists(self.files_root):
            shutil.rmtree(self.files_root)

    def fetch(self):
        status = self.status()
        if status == 'empty':
            self._checkout(self.files_root)
            return True
        elif status == 'modified':
            self.clean_cache()
            self._checkout(self.files_root)
            return True
        elif status == 'outofdate':
            self.clean_cache()
            self._checkout(self.files_root)
            #self._update()
            return True
        elif status == 'downloaded':
            pass
        else:
            pr_warn("Provider status is: '" + status + "'. This shouldn't happen")
            return False
            #TODO: throw an exception here

    def _checkout(self, local_dir):

        #TODO : Sanitize URL
        pr_info("Checking out " + self.repo + " to " + local_dir)
        args = ['clone', '-q', self.repo, local_dir]
        Launcher('git', args).run()
        if self.version:
            args = ['-C', local_dir, 'checkout', '-q', self.version]
            Launcher('git', args).run()

    def status(self):
        if not self.cachable:
            return 'outofdate'
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'

PROVIDER_CLASS = Git
