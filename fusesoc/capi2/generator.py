# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import sys

from fusesoc import utils


class Generator:
    filesets = {}
    parameters = {}
    targets = {}

    def __init__(self, data=None):
        if data is None:
            data = utils.yaml_fread(sys.argv[1])

        self.config = data.get("parameters")
        self.files_root = data.get("files_root")
        self.vlnv = data.get("vlnv")

        # Edalize decide core_file dir. generator creates file
        self.core_file = self.vlnv.split(":")[2] + ".core"

    def add_files(
        self, files, fileset="rtl", targets=["default"], file_type="", logical_name=""
    ):
        if not fileset in self.filesets:
            self.filesets[fileset] = {"files": []}
        self.filesets[fileset]["files"] = files
        self.filesets[fileset]["file_type"] = file_type
        self.filesets[fileset]["logical_name"] = logical_name

        for target in targets:
            if not target in self.targets:
                self.targets[target] = {"filesets": []}
            if not fileset in self.targets[target]["filesets"]:
                self.targets[target]["filesets"].append(fileset)

    def add_parameter(self, parameter, data={}, targets=["default"]):
        self.parameters[parameter] = data

        for target in targets:
            if not target in self.targets:
                self.targets[target] = {}
            if not "parameters" in self.targets[target]:
                self.targets[target]["parameters"] = []
            if not parameter in self.targets[target]["parameters"]:
                self.targets[target]["parameters"].append(parameter)

    def write(self):
        coredata = {
            "name": self.vlnv,
            "filesets": self.filesets,
            "parameters": self.parameters,
            "targets": self.targets,
        }
        return utils.yaml_fwrite(self.core_file, coredata, "CAPI=2:\n")
