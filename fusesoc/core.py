# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import logging

from fusesoc.capi2.core import Core as Capi2Core

logger = logging.getLogger(__name__)


class Core:
    def __new__(cls, *args, **kwargs):
        return Capi2Core(*args, **kwargs)
