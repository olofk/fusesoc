# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import copy

# FIXME: Add IP-XACT support
import logging
import os
import shutil
import warnings
from filecmp import cmp

from fusesoc import utils
from fusesoc.capi2.coredata import CoreData
from fusesoc.provider.provider import get_provider
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)


class Core:
    capi_version = 2

    def __init__(
        self,
        parser,
        core_file,
        cache_root="",
        generated=False,
    ):
        self.core_file = core_file

        self.cache_root = cache_root

        self.core_basename = os.path.basename(self.core_file)
        self.core_root = os.path.dirname(self.core_file)

        # Populated by CoreDB._solve(). TODO: Find a better solution for that.
        self.direct_deps = []

        self._parser = parser

        self.export_files = []

        self._capi_data = self._parser.read(core_file)

        # If original data is needed at some later stage we need to create
        # deepcopy since CoreData might modify it.
        self._coredata = CoreData(copy.deepcopy(self._capi_data))

        self.name = Vlnv(self._coredata.get_name())

        cd_provider = self._coredata.get_provider()

        if cd_provider:
            self.files_root = os.path.join(cache_root, self.name.sanitized_name)
            self.provider = get_provider(cd_provider["name"])(
                cd_provider, self.core_root, self.files_root
            )
        else:
            self.files_root = self.core_root
            self.provider = None

        self.is_generated = generated

    def __repr__(self):
        return str(self.name)

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return "local"

    def export(self, dst_dir, flags={}):
        src_files = [f["name"] for f in self.get_files(flags)]

        for k, v in self._get_vpi(flags).items():
            src_files += [
                f for f in v["src_files"] + v["inc_files"]
            ]  # FIXME include files
        self._debug("Exporting {}".format(str(src_files)))

        filesets = self._coredata.get_filesets(flags)

        for scripts in self._get_script_names(flags).values():
            for script in scripts:
                for fs in script.get("filesets", []):
                    for file in filesets[fs].get("files", []):
                        for filename, attributes in file.items():
                            src_files.append(filename)

        dirs = list(set(map(os.path.dirname, src_files)))
        for d in dirs:
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
        for root, dirs, files in os.walk(dst_dir):
            for f in files:
                _abs_f = os.path.join(root, f)
                if not os.path.relpath(_abs_f, dst_dir).replace("\\", "/") in src_files:
                    os.remove(_abs_f)

    def _get_script_names(self, flags):
        target_name, target = self._get_target(flags)
        hooks = {}

        if "hooks" in target:
            cd_scripts = self._coredata.get_scripts(flags)
            for hook in ["pre_build", "post_build", "pre_run", "post_run"]:
                scripts = target["hooks"][hook] if hook in target["hooks"] else None

                if scripts:
                    hooks[hook] = []
                    for script in scripts:
                        if not script in cd_scripts:
                            raise SyntaxError(
                                "Script '{}', requested by target '{}', was not found".format(
                                    script, target_name
                                )
                            )

                        cd_scripts[script]["name"] = script
                        hooks[hook].append(cd_scripts[script])

        return hooks

    """ Get flags, including tool, from target """

    def get_flags(self, target_name):
        flags = {}

        cd_targets = self._coredata.get_targets(flags)
        if target_name in cd_targets:
            target = cd_targets[target_name]

            if target:
                if "flags" in target:
                    flags = target["flags"].copy()

                if "default_tool" in target:
                    # Special case for tool as we get it from default_tool
                    flags["tool"] = str(target["default_tool"])

        else:
            raise RuntimeError(f"'{self.name}' has no target '{target_name}'")
        return flags

    def get_filters(self, flags):
        target_name, target = self._get_target(flags)
        return target.get("filters", [])

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
                    if (type(v) == bool and v == True)
                    or (type(v) == str and len(v)) > 0
                    or (type(v) == list and len(v)) > 0
                    or (type(v) == dict and len(v)) > 0
                }

                _src_files.append(attributes)
        return _src_files

    def get_generators(self, flags={}):
        cd_generators = self._coredata.get_generators(flags)
        generators = {}
        for k, v in cd_generators.items():
            v.update({"root": self.files_root})
            generators[k] = v

        return generators

    def get_virtuals(self, flags={}):
        """Get a list of "virtual" VLNVs provided by this core."""

        return [Vlnv(x) for x in self._coredata.get_virtual(flags)]

    def get_parameters(self, flags={}, ext_parameters={}):
        def _parse_param_value(name, datatype, default):
            if datatype == "bool":
                if type(default) == str:
                    if default.lower() == "true":
                        return True
                    elif default.lower() == "false":
                        return False
                    else:
                        _s = "{}: Invalid default value '{}' for bool parameter {}"
                        raise SyntaxError(_s.format(self.name, default, p))
                return default
            elif datatype == "int":
                if type(default) == int:
                    return default
                else:
                    return int(default, 0)
            elif datatype == "real":
                if type(default) == float:
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

            if not datatype in ["bool", "file", "int", "real", "str"]:
                _s = "{} : Invalid datatype '{}' for parameter {}"
                raise SyntaxError(_s.format(self.name, datatype, p))

            if not paramtype in [
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
        target_name, target = self._get_target(flags)
        parameters = {}

        if "parameters" in target:
            for _param in target["parameters"]:
                plist = _param.split("=", 1)

                p = plist[0]

                # parse might have left us with an empty string for the parameter name
                # In that case, just go to the next parameter
                if not p:
                    continue

                cd_parameters = self._coredata.get_parameters(flags)

                # The parameter exists either in this core...
                if p in cd_parameters:
                    parameters[p] = _parse_param(flags, p, cd_parameters[p])

                # ...or in any of its dependencies
                elif p in ext_parameters:
                    parameters[p] = ext_parameters[p]
                    datatype = parameters[p]["datatype"]

                else:
                    raise SyntaxError(
                        "Parameter '{}', requested by target '{}', was not found".format(
                            p, target_name
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
                    and type(parameters[p]["default"]) == str
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
            return " ".join(toplevel) if type(toplevel) == list else toplevel
        else:
            s = "{} : Target '{}' has no toplevel"
            raise SyntaxError(s.format(self.name, target_name))

    def get_ttptttg(self, flags):
        self._debug("Getting ttptttg for flags {}".format(str(flags)))
        target_name, target = self._get_target(flags)
        ttptttg = []

        if not target:
            return ttptttg

        _ttptttg = []
        if "generate" in target:
            for f in target["generate"]:
                if type(f) == str:
                    _ttptttg.append({"name": f, "params": {}})
                elif type(f) == dict:
                    for k, v in f.items():
                        _ttptttg.append({"name": k, "params": v})

        if _ttptttg:
            self._debug(f" Matched generator instances {_ttptttg}")
        for gen in _ttptttg:
            gen_name = gen["name"]
            cd_generate = self._coredata.get_generate(flags)
            if not gen_name in cd_generate:
                raise SyntaxError(
                    "Generator instance '{}', requested by target '{}', was not found".format(
                        gen_name, target_name
                    )
                )
            gen_inst = cd_generate[gen_name]
            params = (
                utils.merge_dict(gen_inst["parameters"], gen["params"])
                if "parameters" in gen_inst
                else {}
            )
            t = {
                "name": gen_name,
                "generator": str(gen_inst["generator"]),
                "config": dict(params),
                "pos": str(
                    cd_generate[gen_name]["position"]
                    if "position" in cd_generate[gen_name]
                    else "append"
                ),
            }
            ttptttg.append(t)
        return ttptttg

    def _get_vpi(self, flags):
        vpi = {}
        target_name, target = self._get_target(flags)
        if not target:
            return vpi

        cd_filesets = self._coredata.get_filesets(flags)

        for vpi_name in target.get("vpi", []):
            cd_vpi_lib = self._coredata.get_vpi(flags)
            files = []
            incfiles = []  # Really do this automatically?
            libs = []
            if vpi_name in cd_vpi_lib:
                for fs in cd_vpi_lib[vpi_name].get("filesets", []):
                    for f in cd_filesets[fs]["files"]:
                        for k, v in f.items():
                            if v["is_include_file"]:
                                incfiles.append(k)
                            else:
                                files.append(k)

                for lib in cd_vpi_lib[vpi_name].get("libs", []):
                    libs.append(lib)

            vpi[vpi_name] = {
                "src_files": files,
                "inc_files": incfiles,
                "libs": [l for l in libs],
            }
        return vpi

    def get_vpi(self, flags):
        self._debug(f"Getting VPI libraries for flags {flags}")
        target_name, target = self._get_target(flags)
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

    def info(self):
        s = """CORE INFO
Name:        {}
Description: {}
Core root:   {}
Core file:   {}

Targets:
{}"""

        cd_target = self._coredata.get_targets({})

        if cd_target:
            l = max(len(x) for x in cd_target)
            targets = ""

            for t in sorted(cd_target):
                targets += "{} : {}\n".format(
                    t.ljust(l),
                    cd_target[t]["description"]
                    if "description" in cd_target[t]
                    else "<No description>",
                )
        else:
            targets = "<No targets>"
        return s.format(
            str(self.name),
            str(self.get_description() or "<No description>"),
            str(self.core_root),
            str(self.core_basename),
            targets,
        )

    def patch(self, dst_dir):
        # FIXME: Use native python patch instead
        patches = self.provider.patches
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

    def _get_target(self, flags):
        self._debug(" Resolving target for flags '{}'".format(str(flags)))

        cd_target = self._coredata.get_targets(flags)
        target_name = None
        if flags.get("is_toplevel") and flags.get("target"):
            target_name = flags.get("target")
        else:
            target_name = "default"

        if target_name in cd_target:
            self._debug(f" Matched target {target_name}")
            return target_name, cd_target[target_name]
        else:
            self._debug("Matched no target")
            return target_name, {}

    def _get_filesets(self, flags):
        self._debug("Getting filesets for flags '{}'".format(str(flags)))
        target_name, target = self._get_target(flags)
        if not target:
            return []
        filesets = []

        cd_filesets = self._coredata.get_filesets(flags)

        for fs in target.get("filesets", []):
            if not fs in cd_filesets:
                raise SyntaxError(
                    "{} : Fileset '{}', requested by target '{}', was not found".format(
                        self.name, fs, target_name
                    )
                )
            filesets.append(cd_filesets[fs])

        self._debug(" Matched filesets " + str(target.get("filesets")))
        return filesets

    def get_name(self):
        return self.name

    def get_description(self):
        return self._coredata.get_description()
