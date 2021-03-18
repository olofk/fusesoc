# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging
import os.path

from fusesoc.provider.provider import Provider

logger = logging.getLogger(__name__)


class Local(Provider):
    @staticmethod
    def init_library(library):
        if not os.path.isdir(library.location):
            logger.error(f"Local library at location '{library.location}' not found.")
            exit(1)

    def _checkout(self, local_dir):
        pass

    @staticmethod
    def update_library(library):
        pass
