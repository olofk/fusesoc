# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import pathlib

import pytest

from fusesoc.lockfile import load_lockfile


def test_load_lockfile():
    from fusesoc.vlnv import Vlnv

    lockfile = load_lockfile(
        pathlib.Path(__file__).parent / "lockfiles" / "works.lock.yml"
    )

    assert lockfile == {
        "cores": {
            Vlnv(":lib:pin:0.1"): {"name": Vlnv(":lib:pin:0.1")},
            Vlnv(":lib:gpio:0.1"): {"name": Vlnv(":lib:gpio:0.1")},
            Vlnv(":common:gpio_ctrl:0.1"): {"name": Vlnv(":common:gpio_ctrl:0.1")},
            Vlnv(":product:toppy:0.1"): {"name": Vlnv(":product:toppy:0.1")},
        },
    }


def test_load_lockfile_duplicates():
    with pytest.raises(SyntaxError):
        _ = load_lockfile(
            pathlib.Path(__file__).parent / "lockfiles" / "duplicates.lock.yml"
        )
