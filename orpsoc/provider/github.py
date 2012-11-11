from orpsoc.provider import Provider
import subprocess
import os.path

class GitHub(Provider):
    def __init__(self, config):
        self.user   = config.get('user')
        self.repo   = config.get('repo')
        self.branch = config.get('branch')

    def fetch(self, local_dir):
        status = self.status(local_dir)
        if status == 'empty':
            self._checkout(local_dir)
        elif status == 'modified':
            self.clean_cache()
            self._checkout(local_dir)
        elif status == 'outofdate':
            self._update()
        elif status == 'downloaded':
            pass
        else:
            print("Something else is wrong")

    def _checkout(self, local_dir):
        try:
            #FIXME: Add support for checking out a certain revision
            repo = 'git://github.com/'+self.user+'/'+self.repo+'.git'
            subprocess.check_call(['git', 'clone', '--depth','1',
                                   '--branch', self.branch, repo],
                                  cwd = os.path.split(local_dir)[0])
        except OSError:
            print("Error: Command git not found. Make sure it is in $PATH")
            exit(1)
        except subprocess.CalledProcessError:
            print("Error: Failed to clone git repository")
            exit(1)

    def status(self, local_dir):
        if not os.path.isdir(local_dir):
            return 'empty'
        else:
            return 'downloaded'
