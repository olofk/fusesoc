# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import io
import logging
import os.path
import tarfile
import urllib.parse as urlparse

import requests

from fusesoc.provider.provider import Provider

_HAS_TAR_FILTER = hasattr(tarfile, "tar_filter")  # Requires Python 3.12

logger = logging.getLogger(__name__)


class Gitlab(Provider):
    def _checkout(self, local_dir):
        host = self.config.get("host", "gitlab.com")
        project = self.config.get("project")
        ref = self.config.get("ref", "main")

        logger.info(f"Downloading {project} from {host}")

        # Encode the project path in case there are slashes
        project = urlparse.quote_plus(project)
        url = urlparse.quote(
            f"https://{host}/api/v4/projects/{project}"
            + f"/repository/archive.tar.gz?sha={ref}"
        )

        # Check for common authentication tokens in the environment
        if "GITLAB_TOKEN" in os.environ:
            headers = {"Private-Token": os.environ["GITLAB_TOKEN"]}
        elif "CI_JOB_TOKEN" in os.environ:
            headers = {"Job-Token": os.environ["CI_JOB_TOKEN"]}
        else:
            headers = {}

        response = requests.get(url, headers=headers)
        archive = tarfile.open(fileobj=io.BytesIO(response.content), mode="r:gz")

        (cache_root, core) = os.path.split(local_dir)

        # Ugly hack to get the first part of the directory name of the extracted files
        cache_name = archive.getnames()[0]
        extraction_arguments = {"path": cache_root}

        if _HAS_TAR_FILTER:
            extraction_arguments["filter"] = "data"

        archive.extractall(**extraction_arguments)
        os.rename(os.path.join(cache_root, cache_name), os.path.join(cache_root, core))
