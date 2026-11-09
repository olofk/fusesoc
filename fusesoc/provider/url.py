# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import hashlib
import logging
import os.path
import shutil
import sys
import tarfile
import urllib.request as urllib
import zipfile
from urllib.error import HTTPError, URLError

from fusesoc.library import Library
from fusesoc.provider.provider import Provider

logger = logging.getLogger(__name__)

_HAS_TAR_FILTER = hasattr(tarfile, "tar_filter")  # Requires Python 3.12

# Read size when hashing a download.
_HASH_CHUNK_SIZE = 1 << 20


class Url(Provider):
    @staticmethod
    def init_library(library: Library) -> None:
        try:
            logger.info(f"Downloading library from {library.sync_uri}...")
            Url._download(library.sync_uri, library.location, "zip")
            logger.info(f"Library stored at {library.location}")
        except Exception as e:
            raise RuntimeError(str(e))

    @staticmethod
    def update_library(library: Library) -> None:
        try:
            Url._download(library.sync_uri, library.location, "zip")
        except Exception as e:
            raise RuntimeError(str(e))

    def _checkout(self, local_dir):
        url = self.config.get("url")
        logger.info("Downloading...")
        user_agent = self.config.get("user-agent")
        filetype = self.config.get("filetype")
        if not self.config.get("verify_cert", True):
            import ssl

            ssl._create_default_https_context = ssl._create_unverified_context  # type: ignore[assignment, ty:invalid-assignment]

        Url._download(url, local_dir, filetype, user_agent, self.config.get("sha256"))

    @staticmethod
    def _download(url, local_dir, filetype, user_agent=False, sha256=None):
        """Download `url` and unpack it into `local_dir`.

        A given `sha256` must match the downloaded file, checked before it is
        unpacked.
        """
        if user_agent and sys.version_info[0] >= 3:
            opener = urllib.build_opener()
            opener.addheaders = [("User-agent", user_agent)]
            urllib.install_opener(opener)
        try:
            (filename, headers) = urllib.urlretrieve(url)
        except (URLError, HTTPError) as e:
            raise RuntimeError(f"Failed to download '{url}'. '{e.reason}'")

        if sha256:
            # TODO: use hashlib.file_digest (Python 3.11+) once 3.10 is dropped.
            h = hashlib.sha256()
            with open(filename, "rb") as f:
                for chunk in iter(lambda: f.read(_HASH_CHUNK_SIZE), b""):
                    h.update(chunk)
            found = h.hexdigest()
            if sha256.lower() != found:
                raise RuntimeError(
                    f"sha256 mismatch for '{url}': expected {sha256.lower()}, found {found}"
                )

        if filetype == "tar":
            t = tarfile.open(filename)
            if _HAS_TAR_FILTER:
                t.extractall(path=local_dir, filter="data")
            else:
                t.extractall(path=local_dir)
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
