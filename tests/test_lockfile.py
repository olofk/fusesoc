# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import pytest


def test_load_lockfile():
    import os

    from fusesoc.lockfile import load_lockfile
    from fusesoc.vlnv import Vlnv

    lockfile_dir = os.path.join(os.path.dirname(__file__), "lockfiles")
    lockfile = load_lockfile(os.path.join(lockfile_dir, "works.lock"))

    assert lockfile == {
        "cores": [
            Vlnv(":lib:pin:0.1"),
            Vlnv(":lib:gpio:0.1"),
            Vlnv(":common:gpio_ctrl:0.1"),
            Vlnv(":product:toppy:0.1"),
        ],
        "virtuals": {
            Vlnv(":interface:pin:"): Vlnv(":lib:pin:0.1"),
            Vlnv(":interface:gpio:"): Vlnv(":lib:gpio:0.1"),
        },
    }
