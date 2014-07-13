import subprocess
import os

class Submodule(object):
    def __init__(self, core_name, config, core_root, cache_root):
        self.repo = config.get('repo')
        self.core_root = core_root
        self.submodule_path = os.path.join(self.core_root, self.repo)
        self.marker = os.path.join(self.submodule_path, '.git')
        self.files_root = self.submodule_path

    def fetch(self):
        status = self.status()
        if status != 'downloaded':
            self._checkout()
        return True

    def _checkout(self):
        pwd = os.getcwd()
        os.chdir(self.core_root)
        subprocess.check_call(['git', 'submodule', 'update', '--init',
            '--remote', '--checkout', self.repo])
        os.chdir(pwd)

    def status(self):
        return 'downloaded' if os.path.isfile(self.marker) else 'empty'

PROVIDER_CLASS = Submodule
