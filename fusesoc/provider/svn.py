# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging

from fusesoc.provider.provider import Provider
from fusesoc.utils import Launcher, cygpath, is_mingw

logger = logging.getLogger(__name__)


class Svn(Provider):
    def _checkout(self, local_dir):
        if is_mingw():
            logger.debug("Using cygpath translation")
            local_dir = cygpath(local_dir)

        args = ["co", "-q"]
        url = self.config.get("url")
        revision_number = self.config.get("revision", None)
        if revision_number:
            logger.info("Downloading %s revision %s", url, revision_number)
            args.extend(["-r", revision_number])
        else:
            logger.info("Downloading %s", url)
        if self.config.get("ignore_externals", False):
            args.append("--ignore-externals")
        args.extend([url, local_dir])

        Launcher("svn", args).run()
