import copy
import enum
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


class LockFileMode(int, enum.Enum):
    """Lock file usage mode"""

    DISABLED = 0
    LOAD = 1
    STORE = 2


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
        return {}

    cores = {}
    for core in lockfile_data.setdefault("cores", []):

        if "name" in core:
            vlnv = Vlnv(core["name"])
            vln = vlnv.vln_str()
            if vln in map(Vlnv.vln_str, cores.keys()):
                raise SyntaxError(f"Core {vln} defined multiple times in lock file")
            core["name"] = vlnv
        else:
            raise SyntaxError(f"Core definition without a name")
        cores[vlnv] = core
    lockfile = {
        "cores": cores,
    }
    return lockfile


class LockFile:
    def __init__(self):
        """Create a empty lock file"""
        self._data = {}
        self._filepath = None
        self.mode = LockFileMode.DISABLED

    @classmethod
    def load(cls, filepath: pathlib.Path, mode: LockFileMode = LockFileMode.STORE):
        """Load lock file from file path"""
        lockfile = LockFile()
        if mode == LockFileMode.DISABLED:
            return lockfile
        lockfile._data = load_lockfile(filepath)
        lockfile._filepath = filepath
        lockfile.mode = mode
        return lockfile

    def store(self):
        """Store the lock file to disk"""
        if self.mode != LockFileMode.STORE:
            return
        if not self._filepath:
            return
        cores = copy.deepcopy(self.cores())
        # format VLNVs as strings
        for core in cores:
            core["name"] = str(core["name"])
        lockfile = {
            "lockfile_version": 1,
            "fusesoc_version": version,
            "cores": cores,
        }
        fusesoc.utils.yaml_fwrite(self._filepath, lockfile)

    def update(self, cores):
        """Update the lock file information"""
        if self.mode != LockFileMode.STORE:
            return False
        changed = False
        current = self._cores()
        for core in cores:
            item = {"name": core.name}
            if core.name in current:
                if item.items() <= current[core.name].items():
                    continue
                else:
                    self._data["cores"][core.name].update(item)
                    changed = True
            else:
                self._data["cores"][core.name] = item
                changed = True
        return changed

    def _cores(self):
        """Return a dictionary of all the cores in the lock file"""
        return self._data.setdefault("cores", {})

    def cores(self):
        """Return a list of all the cores in the lock file"""
        return [item for item in self._cores().values()]

    def cores_vlnv(self):
        """Return a list of all the core VLNVs in the lock file"""
        return [core["name"] for core in self.cores()]

    def core_vlnv_exists(self, vlvn: Vlnv):
        """Check if the core VLNV exists in the lock file"""
        return vlvn in self._cores().keys()

    def no_cores(self):
        """The lock file does not contain any cores"""
        return not bool(self._cores())
