# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import os
import tempfile

from fusesoc.config import Config
from fusesoc.main import init_coremanager

build_root = "test_build_root"

EXAMPLE_CONFIG = """
[main]
ignored_dirs = B nonexistent_dir
"""

EXAMPLE_CORE = """\
CAPI=2:
description: dummy core
name: ::dummy:{version}
"""


def test_ignored_dirs():
    """Check that ignored_dirs works in config files."""
    with tempfile.TemporaryDirectory() as td:
        for dirname, version in [("A", "1.0"), ("B", "2.0")]:
            dir_path = os.path.join(td, dirname)
            core_path = os.path.join(dir_path, "foo.core")

            os.mkdir(dir_path)
            with open(core_path, "w") as core_file:
                core_file.write(EXAMPLE_CORE.format(version=version))

        conf_path0 = os.path.join(td, "0.conf")
        with open(conf_path0, "w") as conf_file0:
            conf_file0.write("")

        conf_path1 = os.path.join(td, "1.conf")
        with open(conf_path1, "w") as conf_file1:
            conf_file1.write(EXAMPLE_CONFIG)

        conf0 = Config(conf_path0)
        assert len(conf0.ignored_dirs) == 0
        cm0 = init_coremanager(conf0, [td])
        assert len(cm0.get_cores()) == 2

        conf1 = Config(conf_path1)
        assert len(conf1.ignored_dirs) == 2
        cm1 = init_coremanager(conf1, [td])
        assert len(cm1.get_cores()) == 1
