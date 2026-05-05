# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

# FIXME: Add IP-XACT support
import logging
import os
import shutil
import warnings
from dataclasses import dataclass, field
from filecmp import cmp
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Mapping, Sequence

from fusesoc import signature, utils
from fusesoc.capi2.core_handle import CoreHandle
from fusesoc.provider.provider import get_provider
from fusesoc.vlnv import Vlnv

from .coreparser import Core2Parser
from .flags import Flags, get_target_name, into_flag_defs
from .schema.common import License
from .schema.core import Core
from .schema.target import Target

logger = logging.getLogger(__name__)


@dataclass
class CoreInterface:
    parser: Core2Parser
    core_file: Path
    cache_root: Path = field(default_factory=Path)
    generated: bool = False
    direct_deps: list = field(init=False, default_factory=list)
    export_files: list = field(init=False, default_factory=list)
    capi_version: Literal[2] = 2

    def __post_init__(self):
        parsed_capi = self.parser.read(self.core_file)

        self.handle = CoreHandle.from_dict(parsed_capi)

        self.name = Vlnv(self.get_data({}).name)

        if provider := self.get_data({}).provider:
            self.files_root = os.path.join(self.cache_root, self.name.sanitized_name)
            self.provider = get_provider(provider.name)(
                provider.model_dump(exclude_unset=True), self.core_root, self.files_root
            )
        else:
            self.files_root = self.core_root
            self.provider = None

    @property
    def core_basename(self) -> str:
        return os.path.basename(self.core_file)

    @property
    def core_root(self) -> str:
        return os.path.dirname(self.core_file)

    def get_data(self, flags: Flags) -> Core[str]:
        defs = into_flag_defs(flags)
        return self.handle.get(defs)

    def get_target(self, flags: Flags) -> Target[str] | None:
        name = get_target_name(flags)
        return self.get_data(flags).targets.get(name)

    def __repr__(self):
        return str(self.name)

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return "local"

    def export(self, dst_dir, flags={}):
        src_files: list[str] = [f["name"] for f in self.get_files(flags)]

        for k, v in self._get_vpi(flags).items():
            src_files += [
                f for f in v["src_files"] + v["inc_files"]
            ]  # FIXME include files
        self._debug("Exporting {}".format(str(src_files)))

        filesets = self.get_data(flags).filesets

        for scripts in self._get_script_names(flags).values():
            for script in scripts:
                for fs in script.get("filesets", []):
                    for file in filesets[fs].files:
                        assert not isinstance(file, str)
                        for filename, attributes in file.items():
                            src_files.append(filename)

        dirs: set[str] = {os.path.dirname(p) for p in src_files}
        for d in dirs:
            if not os.path.isabs(d):
                os.makedirs(os.path.join(dst_dir, d), exist_ok=True)

        for f in src_files:
            if f.startswith(".."):
                warnings.warn(
                    "The file {} in {} is not within the directory containing "
                    "the core file. This is deprecated and will be an error in "
                    "a future FuseSoC version. A typical solution is to move "
                    "core file into the root directory of the IP block it "
                    "describes.".format(f, self.core_file),
                    FutureWarning,
                )
            if not os.path.isabs(f):
                if os.path.exists(os.path.join(self.core_root, f)):
                    src = os.path.join(self.core_root, f)
                elif os.path.exists(os.path.join(self.files_root, f)):
                    src = os.path.join(self.files_root, f)
                else:
                    _dirs = self.core_root
                    if self.files_root != self.core_root:
                        _dirs += " or " + self.files_root
                    raise RuntimeError(f"Cannot find {f} in {_dirs}")

                dst = os.path.join(dst_dir, f)
                # Only update if file is changed or doesn't exist
                if not os.path.exists(dst) or not cmp(src, dst):
                    try:
                        shutil.copy2(src, dst)
                    except IsADirectoryError:
                        shutil.copytree(src, dst, dirs_exist_ok=True)

        # Clean out leftover files from previous builds
        for root, dirs, files in os.walk(dst_dir):  # ty: ignore[invalid-assignment]
            for f in files:
                _abs_f = os.path.join(root, f)
                _rel_f = os.path.normpath(os.path.relpath(_abs_f, dst_dir))

                if _rel_f not in [os.path.normpath(x) for x in src_files]:
                    os.remove(_abs_f)

    def _get_script_names(
        self, flags: Flags
    ) -> Mapping[str, Sequence[Mapping[str, Any]]]:
        target = self.get_target(flags)

        hooks: dict[str, list[dict[str, Any]]] = {}
        if target is not None:
            cd_scripts = self.get_data(flags).scripts
            for hook in ["pre_build", "post_build", "pre_run", "post_run"]:
                if scripts := getattr(target.hooks, hook):
                    hooks[hook] = []
                    for script in scripts:
                        cd_script = cd_scripts.get(script)
                        if cd_script is None:
                            raise SyntaxError(
                                "Script '{}', requested by target '{}', was not found".format(
                                    script, get_target_name(flags)
                                )
                            )

                        hooks[hook].append(cd_script.model_dump() | {"name": script})

        return hooks

    def get_flags(self, target_name: str) -> Flags:
        """Get flags, including tool, from target"""

        target = self.get_data({}).targets.get(target_name)
        if target is None:
            raise RuntimeError(f"'{self.name}' has no target '{target_name}'")

        flags = dict(target.flags)
        if tool := target.default_tool:
            flags["tool"] = tool

        return flags

    def get_filters(self, flags: Flags) -> list[str]:
        return list(target.filters) if (target := self.get_target(flags)) else []

    def get_flow(self, flags):
        self._debug("Getting flow for flags {}".format(str(flags)))
        flow = None
        if flags.get("flow"):
            flow = flags["flow"]
        else:
            _flags = flags.copy()
            _flags["is_toplevel"] = True
            target_name, target = self._get_target(_flags)
            if "flow" in target:
                flow = str(target["flow"])

        if flow:
            self._debug(f" Matched flow {flow}")
        else:
            self._debug(" Matched no flow")
        return flow

    def get_scripts(self, files_root, flags):
        self._debug("Getting hooks for flags '{}'".format(str(flags)))
        hooks = {}
        for hook, scripts in self._get_script_names(flags).items():
            hooks[hook] = []
            for script in scripts:
                env = script.get("env", {})
                env["FILES_ROOT"] = files_root
                _script = {
                    "name": script.get("name", ""),
                    "cmd": [str(x) for x in script.get("cmd", [])],
                    "env": env,
                }
                hooks[hook].append(_script)
                _s = " Matched {} hook {}"
                self._debug(_s.format(hook, str(_script)))
        return hooks

    def get_tool_options(self, flags):
        _flags = flags.copy()

        self._debug("Getting tool options for flags {}".format(str(_flags)))

        target_name, target = self._get_target(_flags)
        tool = flags["tool"]
        options = (
            target["tools"][tool]
            if "tools" in target and tool in target["tools"]
            else {}
        )

        if "tools" in target:
            self._debug("Found tool options " + str(target["tools"]))
        else:
            self._debug("No tool options found")

        return options

    def get_flow_options(self, flags):
        _flags = flags.copy()

        self._debug("Getting flow options for flags {}".format(str(_flags)))
        target_name, target = self._get_target(_flags)

        if "flow_options" in target:
            self._debug("Found flow options " + str(target["flow_options"]))
        else:
            self._debug("Found no flow options")

        return ("flow_options" in target and target["flow_options"]) or {}

    def get_depends(self, flags):  # Add use flags?
        depends = []
        self._debug("Getting dependencies for flags {}".format(str(flags)))
        for fs in self._get_filesets(flags):
            depends += [Vlnv(d) for d in fs["depend"]]
        return depends

    def get_files(self, flags):
        src_files = []
        for fs in self._get_filesets(flags):
            src_files += fs["files"]

        _src_files = []
        for f in src_files:
            for filename, attributes in f.items():
                attributes["name"] = filename

                # Remove all key-value-pairs with values that are either bool with
                # value False or str of length 0
                attributes = {
                    k: v
                    for k, v in attributes.items()
                    if (isinstance(v, bool) and v is True)
                    or (isinstance(v, str) and len(v) > 0)
                    or (isinstance(v, list) and len(v) > 0)
                    or (isinstance(v, dict) and len(v) > 0)
                }

                _src_files.append(attributes)
        return _src_files

    def get_generators(self, flags: Flags = {}) -> Mapping[str, Any]:
        generators = self.get_data(flags).generators
        return {
            name: generator.model_dump(exclude_unset=True) | {"root": self.files_root}
            for name, generator in generators.items()
        }

    def get_virtuals(self, flags: Flags = {}) -> list[Vlnv]:
        """Get a list of "virtual" VLNVs provided by this core."""
        return [Vlnv(name) for name in self.get_data(flags).virtual]

    def get_parameters(self, flags: Flags = {}, ext_parameters={}):
        def _parse_param_value(name, datatype, default):
            if datatype == "bool":
                if isinstance(default, str):
                    if default.lower() == "true":
                        return True
                    elif default.lower() == "false":
                        return False
                    else:
                        _s = "{}: Invalid default value '{}' for bool parameter {}"
                        raise SyntaxError(_s.format(self.name, default, p))
                return default
            elif datatype == "int":
                if isinstance(default, int):
                    return default
                else:
                    return int(default, 0)
            elif datatype == "real":
                if isinstance(default, float):
                    return default
                else:
                    return float(default)
            else:
                return str(default)

        def _parse_param(flags, name, core_param):
            parsed_param = {}
            datatype = core_param["datatype"]
            paramtype = core_param["paramtype"]
            description = (
                core_param["description"] if "description" in core_param else ""
            )

            if datatype not in ["bool", "file", "int", "real", "str"]:
                _s = "{} : Invalid datatype '{}' for parameter {}"
                raise SyntaxError(_s.format(self.name, datatype, p))

            if paramtype not in [
                "cmdlinearg",
                "generic",
                "plusarg",
                "vlogdefine",
                "vlogparam",
            ]:
                _s = "{} : Invalid paramtype '{}' for parameter {}"
                raise SyntaxError(_s.format(self.name, paramtype, p))
            parsed_param = {
                "datatype": str(core_param["datatype"]),
                "paramtype": paramtype,
            }

            if description:
                parsed_param["description"] = str(description)

            if "default" in core_param:
                parsed_param["default"] = _parse_param_value(
                    name, datatype, core_param["default"]
                )

            return parsed_param

        self._debug("Getting parameters for flags '{}'".format(str(flags)))
        target = self.get_target(flags)
        parameters = {}

        if target is not None:
            for _param in target.parameters:
                plist = _param.split("=", 1)

                p = plist[0]

                # parse might have left us with an empty string for the parameter name
                # In that case, just go to the next parameter
                if not p:
                    continue

                cd_parameters = self.get_data(flags).parameters

                # The parameter exists either in this core...
                if p in cd_parameters:
                    cd_parameter = cd_parameters[p].model_dump(exclude_unset=True)
                    parameters[p] = _parse_param(flags, p, cd_parameter)

                # ...or in any of its dependencies
                elif p in ext_parameters:
                    parameters[p] = ext_parameters[p]

                else:
                    raise SyntaxError(
                        "Parameter '{}', requested by target '{}', was not found".format(
                            p, get_target_name(flags)
                        )
                    )

                # Set default value
                if len(plist) > 1:
                    parameters[p]["default"] = _parse_param_value(
                        p, parameters[p]["datatype"], plist[1]
                    )

                # If default is a string and it is empty it should be deleted
                if (
                    "default" in parameters[p]
                    and isinstance(parameters[p]["default"], str)
                    and len(parameters[p]["default"]) == 0
                ):
                    del parameters[p]["default"]

        self._debug(f"Found parameters {parameters}")

        return parameters

    def get_toplevel(self, flags):
        _flags = flags.copy()
        _flags["is_toplevel"] = True  # FIXME: Is this correct?
        self._debug("Getting toplevel for flags {}".format(str(_flags)))
        target_name, target = self._get_target(_flags)

        if "toplevel" in target:
            toplevel = target["toplevel"]
            self._debug(f"Matched toplevel {toplevel}")
            return " ".join(toplevel) if isinstance(toplevel, Sequence) else toplevel
        else:
            s = "{} : Target '{}' has no toplevel"
            raise SyntaxError(s.format(self.name, target_name))

    def get_ttptttg(self, flags):
        self._debug("Getting ttptttg for flags {}".format(str(flags)))
        target_name, target = self._get_target(flags)
        ttptttg = []

        if not target:
            return ttptttg

        _ttptttg: list[tuple[str, dict]] = []
        if "generate" in target:
            for f in target["generate"]:
                if isinstance(f, str):
                    _ttptttg.append((f, {}))
                elif isinstance(f, dict):
                    for k, v in f.items():
                        _ttptttg.append((k, v))

        if _ttptttg:
            self._debug(f" Matched generator instances {_ttptttg}")
        for gen_name, gen_params in _ttptttg:
            cd_generate = self.get_data(flags).generate
            if gen_name not in cd_generate:
                raise SyntaxError(
                    "Generator instance '{}', requested by target '{}', was not found".format(
                        gen_name, target_name
                    )
                )
            gen_inst = cd_generate[gen_name]
            params = utils.merge_dict(dict(gen_inst.parameters), gen_params)
            t = {
                "name": gen_name,
                "generator": gen_inst.generator,
                "config": params,
                "pos": gen_inst.position if gen_inst.position is not None else "append",
            }
            ttptttg.append(t)
        return ttptttg

    def _get_vpi(self, flags):
        vpi = {}
        target_name, target = self._get_target(flags)
        if not target:
            return vpi

        cd_filesets = self.get_data(flags).filesets

        for vpi_name in target.get("vpi", []):
            cd_vpi_lib = self.get_data(flags).vpi
            files = []
            incfiles = []  # Really do this automatically?
            libs = []
            if vpi_name in cd_vpi_lib:
                for fs in cd_vpi_lib[vpi_name].filesets:
                    for f in cd_filesets[fs].files:
                        assert not isinstance(f, str)
                        for k, v in f.items():
                            if v.is_include_file:
                                incfiles.append(k)
                            else:
                                files.append(k)

                libs = list(cd_vpi_lib[vpi_name].libs)

            vpi[vpi_name] = {"src_files": files, "inc_files": incfiles, "libs": libs}
        return vpi

    def get_vpi(self, flags):
        self._debug(f"Getting VPI libraries for flags {flags}")
        vpi = []
        _vpi = self._get_vpi(flags)
        self._debug(" Matched VPI libraries {}".format([v for v in _vpi]))
        for k, v in sorted(_vpi.items()):
            vpi.append(
                {
                    "name": k,
                    "src_files": [f for f in v["src_files"]],
                    "include_dirs": utils.unique_dirs(v["inc_files"]),
                    "libs": v["libs"],
                }
            )
        return vpi

    def info(self, trustfile):
        s = """CORE INFO
Name:        {}
Description: {}
Core root:   {}
Core file:   {}
Signature:   {}

Targets:
{}"""

        if cd_targets := self.get_data({}).targets:
            maxlen = max(len(x) for x in cd_targets)

            targets = ""
            for name in sorted(cd_targets):
                targets += "{} : {}\n".format(
                    name.ljust(maxlen),
                    cd_targets[name].description
                    if "description" in cd_targets[name].description
                    else "<No description>",
                )
        else:
            targets = "<No targets>"
        return s.format(
            str(self.name),
            str(self.get_data({}).description or "<No description>"),
            str(self.core_root),
            str(self.core_basename),
            self.sig_status_long(trustfile),
            targets,
        )

    def patch(self, dst_dir):
        # FIXME: Use native python patch instead
        patches = self.provider.patches  # ty: ignore[unresolved-attribute]
        for f in patches:
            patch_file = os.path.abspath(os.path.join(self.core_root, f))
            if os.path.isfile(patch_file):
                self._debug(
                    "  applying patch file: "
                    + patch_file
                    + "\n"
                    + "                   to: "
                    + os.path.join(dst_dir)
                )
                try:
                    utils.Launcher(
                        "git",
                        [
                            "apply",
                            "--unsafe-paths",
                            "--directory",
                            os.path.join(dst_dir),
                            patch_file,
                        ],
                    ).run()
                except OSError:
                    print("Error: Failed to call external command 'patch'")
                    return False
        return True

    def setup(self):
        if self.provider:
            if self.provider.fetch():
                self.patch(self.files_root)

    def _debug(self, msg):
        logger.debug("{} : {}".format(str(self.name), msg))

    def _get_target(self, flags: Flags):
        self._debug(" Resolving target for flags '{}'".format(str(flags)))

        cd_target = self.get_target(flags)
        target_name = get_target_name(flags)

        if cd_target:
            self._debug(f" Matched target {target_name}")
            return target_name, cd_target.model_dump(exclude_unset=True)
        else:
            self._debug("Matched no target")
            return target_name, {}

    def _get_filesets(self, flags):
        self._debug("Getting filesets for flags '{}'".format(str(flags)))
        target_name, target = self._get_target(flags)
        if not target:
            return []
        filesets = []

        cd_filesets = self.get_data(flags).filesets

        for fs in target.get("filesets", []):
            if fs not in cd_filesets:
                raise SyntaxError(
                    "{} : Fileset '{}', requested by target '{}', was not found".format(
                        self.name, fs, target_name
                    )
                )
            filesets.append(cd_filesets[fs].model_dump())

        self._debug(" Matched filesets " + str(target.get("filesets")))
        return filesets

    def get_description(self) -> str | None:
        return self.get_data({}).description

    def get_license(self) -> str | Mapping[str, str] | None:
        license = self.get_data({}).license
        if isinstance(license, License):
            return license.model_dump()
        return license

    @property
    def mapping(self) -> Mapping[str, str]:
        return MappingProxyType(self.get_data({}).mapping)

    def signed_data(self):
        """
        Return a canonical representation of the core as a string
        for signature purposes.
        """
        file = open(self.core_file, "rb")
        header = file.readline()
        core_raw = file.read()
        file.close()
        if header.startswith(b"CAPI=2:"):
            # Core file is single document, no built in signature.  We
            # sign everything after the header line.
            core_canonical = core_raw.strip()
        else:
            # Core file is not a valid CAPI=2 document.
            raise RuntimeError("File to sign is not a valid CAPI=2 document.")
        return core_canonical

    def sig_status_long(self, trustfile):
        return {
            "-": "Not signed",
            "?": "Signed by unknown key",
            "*": "Signature is not for this core",
            "!": "Signature checking error",
            "good": "Good",
            "?!": "Either signed by an unknown key, or signature does not match",
        }.get(self.sig_status(trustfile), "Other signature checking error")

    def sig_status(self, trustfile):
        sigfile = str(self.core_file) + ".sig"
        if not os.path.isfile(sigfile):
            return "-"  # Not signed
        if not trustfile:
            return "?"  # Signed by unknown key
        ok = False
        try:
            res = signature.verify(self, trustfile, sigfile)
            for user in res:
                if res[user]:
                    ok = True
        except RuntimeError:
            return "*"  # Signature is not for this core (should not happen)
        except Exception:
            return "!"  # Other signature checking error
        if ok:
            return "good"
        else:
            return "?!"  # Either signed by an untrusted key, or
            # signature does not match.
