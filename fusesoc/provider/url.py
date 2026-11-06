# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path
import shutil
import ssl
import tarfile
import tempfile
import urllib.request as urllib
import zipfile
from http.client import HTTPException
from urllib.error import URLError

from fusesoc.library import Library
from fusesoc.provider.provider import Provider

logger = logging.getLogger(__name__)

_HAS_TAR_FILTER = hasattr(tarfile, "tar_filter")  # Requires Python 3.12


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
        verify_cert = self.config.get("verify_cert", True)

        Url._download(url, local_dir, filetype, user_agent, verify_cert)

    @staticmethod
    def _download(url, local_dir, filetype, user_agent=False, verify_cert=True):
        # Only an explicit false turns the check off, not a missing value.
        # Both settings go with this request alone: urlopen builds a private
        # opener for a context, and the header is the request's own.
        context = ssl._create_unverified_context() if verify_cert is False else None
        headers = {"User-agent": user_agent} if user_agent else {}
        request = urllib.Request(url, headers=headers)
        # The download is removed once it is unpacked or copied, also on error
        with tempfile.TemporaryDirectory() as tmp:
            filename = os.path.join(tmp, "download")
            try:
                with (
                    urllib.urlopen(request, context=context) as response,
                    open(filename, "wb") as f,
                ):
                    shutil.copyfileobj(response, f)
                    size = f.tell()
                    expected = response.headers.get("Content-Length")
                    # As urlretrieve does: a connection closed early is no
                    # error to read()
                    if expected is not None and size < int(expected):
                        raise RuntimeError(
                            f"Failed to download '{url}'. "
                            f"Got {size} of {expected} bytes"
                        )
            except URLError as e:
                raise RuntimeError(f"Failed to download '{url}'. '{e.reason}'")
            # A cut-off chunked response (IncompleteRead) or a malformed
            # Content-Length are no OSError
            except (OSError, HTTPException, ValueError) as e:
                raise RuntimeError(f"Failed to download '{url}'. '{e}'")

            if filetype == "tar":
                with tarfile.open(filename) as t:
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
