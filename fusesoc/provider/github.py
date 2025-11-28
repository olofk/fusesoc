# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import netrc
import os.path
import sys
import tarfile

from fusesoc.provider.provider import Provider

_HAS_TAR_FILTER = hasattr(tarfile, "tar_filter")  # Requires Python 3.12

logger = logging.getLogger(__name__)

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
else:
    import urllib

    from urllib2 import URLError

URL = "https://github.com/{user}/{repo}/archive/{version}.tar.gz"


def _setup_github_auth():
    """Install urllib opener with GitHub token auth from .netrc if available."""
    try:
        credentials = netrc.netrc()
        auth = credentials.authenticators("github.com")
        if auth:
            _, _, token = auth

            class TokenAuthHandler(urllib.BaseHandler):
                def __init__(self, token):
                    self.token = token

                def http_request(self, req):
                    req.add_header("Authorization", f"token {self.token}")
                    return req

                https_request = http_request

            opener = urllib.build_opener(TokenAuthHandler(token))
            urllib.install_opener(opener)
            logger.debug("Installed GitHub token auth from .netrc")
    except (FileNotFoundError, netrc.NetrcParseError):
        pass


_setup_github_auth()


class Github(Provider):
    def _checkout(self, local_dir):
        user = self.config.get("user")
        repo = self.config.get("repo")

        version = self.config.get("version", "master")

        # TODO : Sanitize URL
        url = URL.format(user=user, repo=repo, version=version)
        logger.info(f"Downloading {user}/{repo} from github")
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except URLError as e:
            raise RuntimeError(f"Failed to download '{url}'. '{e.reason}'")
        t = tarfile.open(filename)
        (cache_root, core) = os.path.split(local_dir)

        # Ugly hack to get the first part of the directory name of the extracted files
        tmp = t.getnames()[0]

        extraction_arguments = {"path": cache_root}
        if _HAS_TAR_FILTER:
            extraction_arguments["filter"] = "data"
        t.extractall(**extraction_arguments)

        os.rename(os.path.join(cache_root, tmp), os.path.join(cache_root, core))
