from fusesoc.utils import pr_info, pr_warn
import os.path
import shutil
import sys
import tarfile

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
else:
    import urllib
    from urllib2 import URLError

URL = 'https://github.com/{user}/{repo}/archive/{version}.tar.gz'

class GitHub(object):
    def __init__(self, core_name, config, core_root, cache_root):
        self.user   = config.get('user')
        self.repo   = config.get('repo')
        self.branch = config.get('branch')

        self.cachable = True
        if 'cachable' in config:
            self.cachable = not (config.get('cachable') == 'false')
        if 'version' in config:
            self.version = config.get('version')
        else:
            self.version = 'master'
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
        url = URL.format(user=self.user,
                         repo=self.repo,
                         version=self.version)
        pr_info("Downloading {}/{} from github".format(self.user,
                                                       self.repo))
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except URLError as e:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))
        t = tarfile.open(filename)
        (cache_root, core) = os.path.split(local_dir)

        #Ugly hack to get the first part of the directory name of the extracted files
        tmp = t.getnames()[0]
        t.extractall(cache_root)
        os.rename(os.path.join(cache_root, tmp),
                  os.path.join(cache_root, core))

    def status(self):
        if not self.cachable:
            return 'outofdate'
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'

PROVIDER_CLASS = GitHub
