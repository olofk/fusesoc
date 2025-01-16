import copy
import json
import logging
import pathlib

import fastjsonschema

import fusesoc.utils
from fusesoc.version import version
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)

lockfile_schema = """
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "FuseSoC Lockfile",
    "description": "FuseSoC Lockfile",
    "type": "object",
    "properties": {
        "cores": {
            "description": "Cores used in the build",
            "type": "object",
            "patternProperties": {
                "^.+$": {
                    "description": "Core used in the build",
                    "properties": {
                        "virtuals": {
                            "description": "Virtual interfaces implemented by the core",
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                        }
                    }
                }
            }
        },
        "fusesoc_version": {
            "description": "FuseSoC version which generated the lockfile",
            "type": "string"
        },
        "lockfile_version": {
            "description": "Lockfile version",
            "type": "integer"
        }
    }
}
"""


def store_lockfile(cores):

    lockfile = {
        "lockfile_version": 1,
        "fusesoc_version": version,
        "cores": {},
    }
    for core in cores:
        name = str(core.name)
        virtual = [
            f"{vlvn.vendor}:{vlvn.library}:{vlvn.name}" for vlvn in core.get_virtuals()
        ]
        if len(virtual) > 0:
            lockfile["cores"][name] = {"virtuals": virtual}
        else:
            lockfile["cores"][name] = {}
    fusesoc.utils.yaml_fwrite("fusesoc.lock", lockfile)


def load_lockfile():
    from fusesoc.lockfile import lockfile_schema

    lockfile_data = None
    lockfile_path = pathlib.Path("fusesoc.lock")
    if lockfile_path.is_file():
        lockfile_data = fusesoc.utils.yaml_fread(lockfile_path)
        try:
            validator = fastjsonschema.compile(json.loads(lockfile_schema))
            validator(lockfile_data)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"\nError parsing JSON Schema: {e}")
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"\nError validating {e}")

    cores = {}
    virtuals = {}
    if lockfile_data:
        for name, core in lockfile_data["cores"].items():
            vlvn = Vlnv(name)
            core_virtuals = []
            if core and "virtuals" in core:
                core_virtuals = [Vlnv(vname) for vname in core["virtuals"]]
                for vname in core["virtuals"]:
                    virtual_vlvn = Vlnv(vname)
                    virtuals[virtual_vlvn] = vlvn

            cores[vlvn] = {
                "vlvn": vlvn,
                "virtuals": core_virtuals,
            }

    lockfile = {
        "cores": cores,
        "virtuals": virtuals,
    }

    return lockfile
