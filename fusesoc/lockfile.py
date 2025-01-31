import json
import logging
import os
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
            "type": "array",
            "items": {
              "type": "string"
            }
        },
        "virtuals": {
            "description": "Virtual cores used in the build",
            "type": "object",
            "patternProperties": {
                "^.+$": {
                    "description": "Virtual core used in the build",
                    "patternProperties": {
                        "^.+$": {
                            "description": "Core implementing virtual core interface"
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

LOCKFILE_DISABLE = 0
LOCKFILE_ENABLE = 1
LOCKFILE_RESET = 2


def _lockfile_path(root_dir=None):
    filename = "fusesoc.lock"
    if root_dir is None:
        return filename
    else:
        return os.path.join(os.path.dirname(root_dir), filename)


def store_lockfile(cores, root_dir=None):

    lockfile = {
        "lockfile_version": 1,
        "fusesoc_version": version,
        "cores": [],
        "virtuals": {},
    }
    for core in cores:
        name = str(core.name)
        virtuals = [
            f"{vlvn.vendor}:{vlvn.library}:{vlvn.name}" for vlvn in core.get_virtuals()
        ]
        if len(virtuals) > 0:
            for virtual in virtuals:
                lockfile["virtuals"][virtual] = name
        lockfile["cores"].append(name)
    fusesoc.utils.yaml_fwrite(_lockfile_path(root_dir), lockfile)


def load_lockfile(root_dir=None):
    lockfile_data = None
    lockfile_path = pathlib.Path(_lockfile_path(root_dir))
    if lockfile_path.is_file():
        lockfile_data = fusesoc.utils.yaml_fread(lockfile_path)
        try:
            validator = fastjsonschema.compile(json.loads(lockfile_schema))
            validator(lockfile_data)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"\nError parsing JSON Schema: {e}")
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"\nError validating {e}")

    cores = []
    virtuals = {}
    if lockfile_data:
        cores = [Vlnv(core_name) for core_name in lockfile_data["cores"]]
        for virtual_name, core_name in lockfile_data["virtuals"].items():
            virtuals[Vlnv(virtual_name)] = Vlnv(core_name)

    lockfile = {
        "cores": cores,
        "virtuals": virtuals,
    }

    return lockfile
