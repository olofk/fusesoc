import logging
import os.path
import sys
import tarfile
from fusesoc.provider.provider import Provider

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
else:
    import urllib
    from urllib2 import URLError

URL = 'https://github.com/{user}/{repo}/archive/{version}.tar.gz'

class Github(Provider):

    def _checkout(self, local_dir):
        user   = self.config.get('user')
        repo   = self.config.get('repo')

        version = self.config.get('version', 'master')

        #TODO : Sanitize URL
        url = URL.format(user=user,
                         repo=repo,
                         version=version)
        logger.info("Downloading {}/{} from github".format(user,
                                                       repo))
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
