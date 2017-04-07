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

class ProviderURL(Provider):

    def _checkout(self, local_dir):
        url = self.config.get('url')
        logger.info("Checking out " + url + " to " + local_dir)
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except URLError as e:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))
        except HTTPError:
            raise RuntimeError("Failed to download '{}'. '{}'".format(url, e.reason))

        (cache_root, core) = os.path.split(local_dir)

        filetype = self.config.get('filetype')
        if filetype == 'tar':
            t = tarfile.open(filename)
            t.extractall(local_dir)
        elif filetype == 'zip':
            with zipfile.ZipFile(filename, "r") as z:
                z.extractall(local_dir)
        elif filetype == 'simple':
            # Splits the string at the last occurrence of sep, and
            # returns a 3-tuple containing the part before the separator,
            # the separator itself, and the part after the separator.
            # If the separator is not found, return a 3-tuple containing
            # two empty strings, followed by the string itself
            segments = url.rpartition('/')
            self.path = os.path.join(local_dir)
            os.makedirs(self.path)
            self.path = os.path.join(self.path, segments[2])
            shutil.copy2(filename, self.path)
        else:
            raise RuntimeError("Unknown file type '" + filetype + "' in [provider] section")

PROVIDER_CLASS = ProviderURL
