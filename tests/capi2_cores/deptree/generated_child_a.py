# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

from fusesoc.capi2.generator import Generator


class MacroGenerator(Generator):
    def run(self):
        assert self.config["filename"]
        self.add_files([self.config["filename"]], file_type="systemVerilogSource")


if __name__ == "__main__":
    g = MacroGenerator()
    g.run()
    g.write()
