import logging
import os

logger = logging.getLogger(__name__)


class Autotype:
    def run(self, edam, work_root):
        type_map = {
            ".c": "cSource",
            ".cpp": "cppSource",
            ".sv": "systemVerilogSource",
            ".tcl": "tclSource",
            ".v": "verilogSource",
            ".vlt": "vlt",
            ".xdc": "xdc",
        }
        for f in edam["files"]:
            if not "file_type" in f:
                fn = f["name"]
                (_, ext) = os.path.splitext(fn)
                ft = type_map.get(ext, "")
                if ft:
                    f["file_type"] = ft
                    logger.debug(f"Autoassigning file type {ft} to {fn}")
                else:
                    logger.warning("Could not autoassign type for " + fn)
        return edam
