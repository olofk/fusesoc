import logging
import os

logger = logging.getLogger(__name__)


class Autotype:
    def run(self, edam, work_root):
        type_map = {
            # HDL sources
            ".sv": "systemVerilogSource",
            ".v": "verilogSource",
            ".vhd": "vhdlSource",
            ".vhdl": "vhdlSource",
            # Vivado IP
            ".xci": "xci",
            ".bd": "bd",
            # Verilator
            ".vlt": "vlt",
            # Design constraints
            ".sdc": "SDC",  # Synopsys-style
            ".xdc": "xdc",  # Vivado-style
            # Software
            ".c": "cSource",
            ".cpp": "cppSource",
            # Scripts
            ".tcl": "tclSource",
            # Register map definitions
            ".rdl": "systemRDL",
        }
        for f in edam["files"]:
            if "file_type" not in f:
                fn = f["name"]
                (_, ext) = os.path.splitext(fn)
                ft = type_map.get(ext, "")
                if ft:
                    f["file_type"] = ft
                    logger.debug(f"Autoassigning file type {ft} to {fn}")
                else:
                    logger.warning("Could not autoassign type for " + fn)
        return edam
