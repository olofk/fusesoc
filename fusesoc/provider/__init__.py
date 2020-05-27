# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from importlib import import_module


def get_provider(name):
    return getattr(import_module("{}.{}".format(__name__, name)), name.capitalize())
