import logging
import os.path
import sys
import tarfile
import zipfile
import shutil

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
    from urllib.error import HTTPError
else:
    import urllib
    from urllib2 import URLError
    from urllib2 import HTTPError

from fusesoc.provider.provider import Provider

class Url(Provider):

    def _checkout(self, local_dir):
        url = self.config.get('url')
        logger.info("Downloading...")
        user_agent = self.config.get('user-agent')
        if user_agent and sys.version_info[0] >= 3:
            opener = urllib.build_opener()
            opener.addheaders = [('User-agent', user_agent)]
            urllib.install_opener(opener)
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except (URLError, HTTPError) as e:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))

        filetype = self.config.get('filetype')
        if filetype == 'tar':
            t = tarfile.open(filename)
            t.extractall(local_dir)
        elif filetype == 'zip':
            with zipfile.ZipFile(filename, "r") as z:
                z.extractall(local_dir)
        elif filetype == 'simple':
            _filename = url.rsplit('/', 1)[1]
            os.makedirs(local_dir)
            shutil.copy2(filename, os.path.join(local_dir, _filename))
        else:
            raise RuntimeError("Unknown file type '" + filetype + "' in [provider] section")
