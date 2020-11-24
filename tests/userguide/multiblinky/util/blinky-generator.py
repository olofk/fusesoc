# This file is public domain, it can be freely copied without restrictions.
# SPDX-License-Identifier: CC0-1.0

import sys
import yaml

MODULE_HEADER = """
module multiblinky #(
  parameter clk_freq_hz = 1_000_000_000
)(
  input clk,
  input rst_n,
  output logic [63:0] q
);
"""

BLINKY_INSTANTIATION = """
blinky #(
  .clk_freq_hz(clk_freq_hz)
) u_blinky_{i} (
  .clk,
  .rst_n,
  .q (q[{i}])
);
"""

MODULE_FOOTER = """
endmodule
"""

CAPI_FILE = """CAPI=2:
name: "{vlnv}"

filesets:
  rtl:
    files:
      - multiblinky.sv
    file_type: systemVerilogSource
    depend:
      - fusesoc:examples:blinky

targets:
  default: &default
    filesets:
      - rtl
    toplevel: multiblinky

parameters:
  clk_freq_hz:
    datatype: int
    paramtype: vlogparam
"""


def main():
    # Data is passed from FuseSoC to the generator as GAPI file (a file in YAML
    # syntax). The path to this file is passed as first command line argument.
    gapi_filepath = sys.argv[1]
    print(gapi_filepath)
    with open(gapi_filepath) as f:
        gapi = yaml.safe_load(f)

    # The following logic assumes the GAPI file in version 1.0 (no other
    # versions exist currently).
    assert gapi["gapi"] == "1.0"

    # Read the parameter `blinky_count` from the GAPI file. Only values between
    # 1 and 64 are valid.
    blinky_count = 1
    if "parameters" in gapi and "blinky_count" in gapi["parameters"]:
        blinky_count = gapi["parameters"]["blinky_count"]
    assert blinky_count >= 1 and blinky_count <= 64

    # Write a SystemVerilog file `multiblinky.sv`, containing `blinky_count`
    # instances of the `blinky` module.
    with open("multiblinky.sv", "w") as sv_file:
        sv_file.write(MODULE_HEADER.format(blinky_count=blinky_count))

        for i in range(blinky_count):
            sv_file.write(BLINKY_INSTANTIATION.format(i=i))

        sv_file.write(MODULE_FOOTER)

    # Write a core file `gen-multiblinky.core`.
    with open("gen-multiblinky.core", "w") as core_file:
        core_file.write(CAPI_FILE.format(vlnv=gapi["vlnv"]))


if __name__ == "__main__":
    main()
