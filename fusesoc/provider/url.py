# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import shutil
import sys
import tarfile
import zipfile

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import HTTPError, URLError
else:
    import urllib
    from urllib2 import URLError
    from urllib2 import HTTPError

from fusesoc.provider.provider import Provider


class Url(Provider):
    def _checkout(self, local_dir):
        url = self.config.get("url")
        logger.info("Downloading...")
        user_agent = self.config.get("user-agent")
        if not self.config.get("verify_cert", True):
            import ssl

            ssl._create_default_https_context = ssl._create_unverified_context

        if user_agent and sys.version_info[0] >= 3:
            opener = urllib.build_opener()
            opener.addheaders = [("User-agent", user_agent)]
            urllib.install_opener(opener)
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except (URLError, HTTPError) as e:
            raise RuntimeError(f"Failed to download '{url}'. '{e.reason}'")

        filetype = self.config.get("filetype")
        if filetype == "tar":
            t = tarfile.open(filename)
            t.extractall(local_dir)
        elif filetype == "zip":
            with zipfile.ZipFile(filename, "r") as z:
                z.extractall(local_dir)
        elif filetype == "simple":
            _filename = url.rsplit("/", 1)[1]
            os.makedirs(local_dir)
            shutil.copy2(filename, os.path.join(local_dir, _filename))
        else:
            raise RuntimeError(
                "Unknown file type '" + filetype + "' in [provider] section"
            )
