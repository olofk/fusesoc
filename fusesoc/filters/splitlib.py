import logging
import os

logger = logging.getLogger(__name__)


def flatten_vlnv(vlnv):
    return str(vlnv).lstrip(":").replace(":", "_").replace(".", "_")


class Splitlib:
    def run(self, edam, work_root):
        libdeps = {}
        for k, v in edam["dependencies"].items():
            libdeps[flatten_vlnv(k)] = [flatten_vlnv(x) for x in v]

        libdeps.update(edam["flow_options"].get("library_dependencies", {}))

        edam["library_dependencies"] = libdeps
        for f in edam["files"]:
            if not "logical_name" in f:
                f["logical_name"] = flatten_vlnv(f["core"])
        return edam
