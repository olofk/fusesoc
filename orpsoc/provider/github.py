from orpsoc.provider import Provider
import subprocess
import os.path
import sys
import tarfile

if sys.version_info[0] >= 3:
    import urllib.request as urllib
else:
    import urllib

class GitHub(Provider):
    def __init__(self, config):
        self.user   = config.get('user')
        self.repo   = config.get('repo')
        self.branch = config.get('branch')
        if 'version' in config:
            self.version = config.get('version')
        else:
            self.version = 'master'

    def fetch(self, local_dir, core_name):
        status = self.status(local_dir)
        if status == 'empty':
            self._checkout(local_dir)
            return True
        elif status == 'modified':
            self.clean_cache()
            self._checkout(local_dir)
            return True
        elif status == 'outofdate':
            self._update()
            return True
        elif status == 'downloaded':
            pass
        else:
            print("Something else is wrong")
            return False
            #TODO: throw an exception here 

    def _checkout(self, local_dir):
        #TODO : Sanitize URL
        url = 'https://github.com/{user}/{repo}/archive/{version}.tar.gz'.format(user=self.user, repo=self.repo, version=self.version)
        (filename, headers) = urllib.urlretrieve(url)

        t = tarfile.open(filename)
        (cache_root, core) = os.path.split(local_dir)

        #Ugly hack to get the first part of the directory name of the extracted files
        tmp = t.getnames()[0]
        t.extractall(cache_root)
        os.rename(os.path.join(cache_root, tmp),
                  os.path.join(cache_root, core))

    def status(self, local_dir):
        if not os.path.isdir(local_dir):
            return 'empty'
        else:
            return 'downloaded'
