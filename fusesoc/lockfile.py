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


def load_lockfile(filepath: pathlib.Path):
    lockfile_data = None
    try:
        lockfile_data = fusesoc.utils.yaml_fread(filepath)
        try:
            validator = fastjsonschema.compile(json.loads(lockfile_schema))
            validator(lockfile_data)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"\nError parsing JSON Schema: {e}")
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"\nError validating {e}")
    except FileNotFoundError:
        return None

    cores = []
    virtuals = {}
    if lockfile_data:
        if "cores" in lockfile_data:
            cores = [Vlnv(core_name) for core_name in lockfile_data["cores"]]
        if "virtuals" in lockfile_data:
            for virtual_name, core_name in lockfile_data["virtuals"].items():
                virtuals[Vlnv(virtual_name)] = Vlnv(core_name)

    lockfile = {
        "cores": cores,
        "virtuals": virtuals,
    }

    return lockfile
