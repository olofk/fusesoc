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
                "type": "object",
                "properties": {
                  "name": {
                    "description": "Core VLVN",
                    "type": "string"
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
    try:
        lockfile_data = fusesoc.utils.yaml_fread(filepath)
        try:
            validator = fastjsonschema.compile(
                json.loads(lockfile_schema), detailed_exceptions=False
            )
            validator(lockfile_data)
        except fastjsonschema.JsonSchemaDefinitionException as e:
            raise SyntaxError(f"Error parsing JSON Schema: {e}")
        except fastjsonschema.JsonSchemaException as e:
            raise SyntaxError(f"Error validating {e}")
    except FileNotFoundError:
        logger.warning(f"Lockfile {filepath} not found")
        return None

    cores = {}
    for core in lockfile_data.setdefault("cores", []):
        if "name" in core:
            vlnv = Vlnv(core["name"])
            vln = vlnv.vln_str()
            if vln in map(Vlnv.vln_str, cores.keys()):
                raise SyntaxError(f"Core {vln} defined multiple times in lock file")
            cores[vlnv] = {"name": vlnv}
        else:
            raise SyntaxError(f"Core definition without a name")
    lockfile = {
        "cores": cores,
    }
    return lockfile
