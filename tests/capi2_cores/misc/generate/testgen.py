# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import sys

import yaml

template = """CAPI=2:
name : {}
targets:
  default:
    parameters: [p]
parameters:
  p:
    datatype : str
    paramtype : vlogparam
"""

with open(sys.argv[1]) as fin:
    data = yaml.safe_load(fin)
    config = data.get("parameters")
    files_root = data.get("files_root")
    vlnv = data.get("vlnv")

with open("generated.core", "w") as fout:
    fout.write(template.format(vlnv))
