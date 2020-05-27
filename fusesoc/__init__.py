# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

try:
    from fusesoc.version import version as __version__
except ImportError:
    __version__ = "unknown"
