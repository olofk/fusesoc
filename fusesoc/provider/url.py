from fusesoc.utils import pr_info, pr_warn
import os.path
import sys
import tarfile
import zipfile
import shutil
import logging

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
    from urllib.error import HTTPError
else:
    import urllib
    from urllib2 import URLError
    from urllib2 import HTTPError

class ProviderURL(object):
    def __init__(self, core_name, config, core_root, cache_root):
        self.url      = config.get('url')
        self.filetype = config.get('filetype')
        if 'corename' in config:
            self.version = config.get('corename')
        else:
            self.version = core_name
        self.files_root = cache_root

    def fetch(self):
        status = self.status()
        if status == 'empty':
            try:
                self._checkout(self.files_root, self.version)
                return True
            except RuntimeError:
                raise
        elif status == 'modified':
            self.clean_cache()
            try:
                self._checkout(self.files_root, self.version)
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

    def _checkout(self, local_dir, core_name):
        pr_info("Checking out " + self.url + " to " + local_dir)
        try:
            (filename, headers) = urllib.urlretrieve(self.url)
        except URLError as e:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))
        except HTTPError:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))

        (cache_root, core) = os.path.split(local_dir)

        if self.filetype == 'tar':
            t = tarfile.open(filename)
            t.extractall(local_dir)
        elif self.filetype == 'zip':
            with zipfile.ZipFile(filename, "r") as z:
                z.extractall(local_dir)
        elif self.filetype == 'simple':
            # Splits the string at the last occurrence of sep, and
            # returns a 3-tuple containing the part before the separator,
            # the separator itself, and the part after the separator.
            # If the separator is not found, return a 3-tuple containing
            # two empty strings, followed by the string itself
            segments = self.url.rpartition('/')
            self.path = os.path.join(local_dir)
            os.makedirs(self.path)
            self.path = os.path.join(self.path, segments[2])
            shutil.copy2(filename, self.path)
        else:
            raise RuntimeError("Unknown file type '" + self.filetype + "' in [provider] section")


    def status(self):
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'

PROVIDER_CLASS = ProviderURL
