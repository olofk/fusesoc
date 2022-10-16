# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

# FIXME: Add IP-XACT support
import logging
import os
import shutil
import warnings

import yaml

try:
    from edalize.edatool import get_edatools
except ImportError:
    from edalize import get_edatools

from fusesoc import utils
from fusesoc.capi2.exprs import Exprs
from fusesoc.provider import get_provider
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)


class File:
    def __init__(self, tree):
        self.copyto = ""
        self.file_type = ""
        self.is_include_file = False
        self.include_path = None
        self.logical_name = ""
        if type(tree) is dict:
            for k, v in tree.items():
                self.name = StringWithUseFlags(os.path.expandvars(k))
                self.file_type = v.get("file_type", "")
                self.is_include_file = v.get("is_include_file", False)
                self.include_path = v.get("include_path")
                self.copyto = v.get("copyto", "")
                self.logical_name = v.get("logical_name", "")
        else:
            self.name = StringWithUseFlags(os.path.expandvars(tree))
            self.is_include_file = False  # "FIXME"


class Genparams(dict):
    pass


class AnyType(str):
    pass


class Any:
    def __new__(self, thing):
        return thing


class StringWithUseFlags(str):
    """A parsed string with support for use flags."""

    def __init__(self, string):
        self.exprs = None

    def parse(self, flags):
        if self.exprs is None:
            self.exprs = Exprs(str(self))
        return self.exprs.expand(flags)


class String(str):
    """A plain (unparsed) string."""

    def parse(self, flags):
        raise RuntimeError(
            "BUG: Attempted to parse a plain string. This is a bug in FuseSoC. "
            "Please file an issue at "
            "https://github.com/olofk/fusesoc/issues/new."
        )


class Integer(int):
    pass


class StringWithUseFlagsOrList:
    def __new__(cls, *args, **kwargs):
        if type(args[0]) == list:
            return [StringWithUseFlags(s) for s in args[0]]
        elif type(args[0]) == str:
            return [StringWithUseFlags(args[0])]


class StringWithUseFlagsOrDict:
    def __init__(self, tree):
        self.params = {}
        if type(tree) is dict:
            for k, v in tree.items():
                self.params = v
                self.name = StringWithUseFlags(k)
        else:
            self.name = StringWithUseFlags(tree)


type_mapping = {
    "String": [str],
    "StringWithUseFlags": [str],
    "StringWithUseFlagsOrDict": [str, dict],
    "StringWithUseFlagsOrList": [str, list],
    "Vlnv": [str],
}


class Section:
    members = {}
    lists = {}
    dicts = {}

    def __init__(self, tree):
        for k, v in sorted(tree.items()):
            if v is None:
                continue
            if k in self.members:
                if self.members[k] in type_mapping.keys() and not any(
                    isinstance(v, t) for t in type_mapping[self.members[k]]
                ):
                    raise SyntaxError(
                        f"Object in {k} section must be a {self.members[k]}"
                    )
                setattr(self, k, globals()[self.members[k]](v))
            elif k in self.lists:
                if not isinstance(v, list):
                    raise SyntaxError(f"Object in '{k}' section must be a list")
                if k.endswith("_append"):
                    _k = k[:-7]
                    _l = getattr(self, _k, [])[:]
                else:
                    _k = k
                    _l = []
                for _item in v:
                    try:
                        _l.append(globals()[self.lists[_k]](_item))
                    except TypeError as e:
                        raise SyntaxError(f"Bad option '{_item}' in section '{k}'")
                setattr(self, _k, _l)
            elif k in self.dicts:
                if not isinstance(v, dict):
                    raise SyntaxError(f"Object in '{k}' section must be a dict")
                _d = {}
                for _name, _items in v.items():
                    try:
                        _d[_name] = globals()[self.dicts[k]](_items)
                    except AttributeError as e:
                        raise SyntaxError(f"Bad option '{_name}' in section '{k}'")
                    try:
                        setattr(_d[_name], "name", _name)
                    except AttributeError:
                        # e.g. bool objects can't set a "name" attribute
                        pass
                setattr(self, k, _d)
            else:
                logger.warning(
                    "Unknown item " + k + " in section " + self.__class__.__name__
                )


class Provider:
    def __new__(cls, *args, **kwargs):
        provider_name = args[0]["name"]
        if provider_name is None:
            raise RuntimeError('Missing "name" in section [provider]')
        return get_provider(provider_name)(
            args[0],
            "FIXME: core_root is used by local providers",
            "FIXME: cache_root can be set in fetch call",
        )


class Core:
    capi_version = 2

    def __init__(self, core_file, cache_root="", generated=False):
        self.core_file = core_file

        basename = os.path.basename(self.core_file)

        self.core_root = os.path.dirname(self.core_file)

        # Populated by CoreDB._solve(). TODO: Find a better solution for that.
        self.direct_deps = []

        try:
            _root = Root(utils.yaml_fread(self.core_file))
        except KeyError as e:
            raise SyntaxError(f"Unknown item {e}")
        except (yaml.scanner.ScannerError, yaml.constructor.ConstructorError) as e:
            raise SyntaxError(str(e))
        except AttributeError as e:
            raise SyntaxError("Error while trying to parse the core file: " + str(e))
        for i in _root.members:
            setattr(self, i, getattr(_root, i))
        for i in _root.lists:
            setattr(self, i, getattr(_root, i))
        for i in _root.dicts:
            setattr(self, i, getattr(_root, i))

        self.export_files = []
        if not self.name:
            raise SyntaxError("Missing 'name' parameter")
        self.sanitized_name = self.name.sanitized_name

        for fs in self.filesets.values():
            if fs.file_type:
                for f in fs.files:
                    if not f.file_type:
                        f.file_type = str(fs.file_type)
            if fs.logical_name:
                for f in fs.files:
                    if not f.logical_name:
                        f.logical_name = str(fs.logical_name)

        if self.provider:
            self.files_root = os.path.join(cache_root, self.sanitized_name)
            # Ugly hack. Don't like injecting vars
            # How about a setup function or setters?
            self.provider.core_root = self.core_root
            self.provider.files_root = self.files_root
        else:
            self.files_root = self.core_root

        self.is_generated = generated

    def __repr__(self):
        return str(self.name)

    def cache_status(self):
        if self.provider:
            return self.provider.status()
        else:
            return "local"

    def export(self, dst_dir, flags={}):
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        src_files = [f["name"] for f in self.get_files(flags)]

        for k, v in self._get_vpi(flags).items():
            src_files += [
                f.name for f in v["src_files"] + v["inc_files"]
            ]  # FIXME include files
        self._debug("Exporting {}".format(str(src_files)))

        for scripts in self._get_script_names(flags).values():
            for script in scripts:
                for fs in script.filesets:
                    src_files += [f.name for f in self.filesets[fs].files]

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
                    dst = os.path.join(dst_dir, f)
                    try:
                        shutil.copyfile(src, dst)
                    except IsADirectoryError:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                elif os.path.exists(os.path.join(self.files_root, f)):
                    src = os.path.join(self.files_root, f)
                    dst = os.path.join(dst_dir, f)
                    try:
                        shutil.copyfile(src, dst)
                    except IsADirectoryError:
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    raise RuntimeError(
                        "Cannot find %s in :\n\t%s\n\t%s"
                        % (f, self.files_root, self.core_root)
                    )

    def _get_script_names(self, flags):
        target = self._get_target(flags)
        hooks = {}

        if target and target.hooks:
            for hook in ["pre_build", "post_build", "pre_run", "post_run"]:
                scripts = getattr(target.hooks, hook)
                if scripts:
                    hooks[hook] = []
                    for script in self._parse_list(flags, scripts):
                        if not script in self.scripts:
                            raise SyntaxError(
                                "Script '{}', requested by target '{}', was not found".format(
                                    script, target.name
                                )
                            )
                        hooks[hook].append(self.scripts[script])

        return hooks

    """ Get flags, including tool, from target """

    def get_flags(self, target_name):
        flags = {}
        target = self.targets.get(target_name)

        if target:
            flags = target.flags.copy()
            # Special case for tool as we get it from default_tool
            if target.default_tool:
                flags["tool"] = str(target.default_tool)
        return flags

    def get_flow(self, flags):
        self._debug("Getting flow for flags {}".format(str(flags)))
        flow = None
        if flags.get("flow"):
            flow = flags["flow"]
        else:
            _flags = flags.copy()
            _flags["is_toplevel"] = True
            target = self._get_target(_flags)
            if target and target.flow:
                flow = str(target.flow)

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
                env = script.env
                env["FILES_ROOT"] = files_root
                _script = {
                    "name": script.name,
                    "cmd": [str(x) for x in script.cmd],
                    "env": env,
                }
                hooks[hook].append(_script)
                _s = " Matched {} hook {}"
                self._debug(_s.format(hook, str(_script)))
        return hooks

    def get_tool_options(self, flags):
        _flags = flags.copy()

        self._debug("Getting tool options for flags {}".format(str(_flags)))
        target = self._get_target(_flags)
        section = None
        try:
            section = getattr(target.tools, flags["tool"])
        except AttributeError:
            pass

        options = {}
        if section:
            for member in section.members:
                if hasattr(section, member):
                    _member = getattr(section, member)
                    if _member:
                        options[member] = str(_member)
            for member in section.lists:
                if hasattr(section, member):
                    _member = getattr(section, member)
                    if _member:
                        options[member] = [str(x) for x in _member]
        self._debug("Found tool options {}".format(str(options)))
        return options

    def get_flow_options(self, flags):
        _flags = flags.copy()

        self._debug("Getting flow options for flags {}".format(str(_flags)))
        target = self._get_target(_flags)

        if target and target.flow_options:
            self._debug(f"Found flow options {target.flow_options}")
        else:
            self._debug("Found no flow options")

        return (target and target.flow_options) or {}

    def get_depends(self, flags):  # Add use flags?
        depends = []
        self._debug("Getting dependencies for flags {}".format(str(flags)))
        for fs in self._get_filesets(flags):
            depends += [Vlnv(d) for d in self._parse_list(flags, fs.depend)]
        return depends

    def get_files(self, flags):
        src_files = []
        for fs in self._get_filesets(flags):
            src_files += fs.files
        _src_files = []
        for f in src_files:
            pf = f.name.parse(flags)
            if pf:
                _f = {}
                for k, v in vars(f).items():
                    if v:
                        _f[k] = v
                _f["name"] = pf
                _src_files.append(_f)
        return _src_files

    def get_generators(self):
        generators = {}
        for k, v in self.generators.items():
            generators[k] = v
            generators[k].root = self.files_root
        return generators

    def get_virtuals(self):
        """Get a list of "virtual" VLNVs provided by this core."""
        return self.virtual

    def get_parameters(self, flags={}, ext_parameters={}):
        def _parse_param_value(name, datatype, default):
            if datatype == "bool":
                if default.lower() == "true":
                    return True
                elif default.lower() == "false":
                    return False
                else:
                    _s = "{}: Invalid default value '{}' for bool parameter {}"
                    raise SyntaxError(_s.format(self.name, default, p))
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
            datatype = core_param.datatype
            description = core_param.description
            paramtype = core_param.paramtype.parse(flags)

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
                "datatype": str(core_param.datatype),
                "paramtype": paramtype,
            }

            if description:
                parsed_param["description"] = str(description)

            if core_param.default:
                parsed_param["default"] = _parse_param_value(
                    name, datatype, core_param.default
                )

            return parsed_param

        self._debug("Getting parameters for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        parameters = {}

        if target:
            for _param in target.parameters:
                plist = _param.parse(flags).split("=", 1)

                p = plist[0]

                # parse might have left us with an empty string for the parameter name
                # In that case, just go to the next parameter
                if not p:
                    continue

                # The parameter exists either in this core...
                if p in self.parameters:
                    parameters[p] = _parse_param(flags, p, self.parameters[p])

                # ...or in any of its dependencies
                elif p in ext_parameters:
                    parameters[p] = ext_parameters[p]
                    datatype = parameters[p]["datatype"]

                else:
                    raise SyntaxError(
                        "Parameter '{}', requested by target '{}', was not found".format(
                            p, target.name
                        )
                    )

                # Set default value
                if len(plist) > 1:
                    parameters[p]["default"] = _parse_param_value(
                        p, parameters[p]["datatype"], plist[1]
                    )

            self._debug(f"Found parameters {parameters}")
        return parameters

    def get_toplevel(self, flags):
        _flags = flags.copy()
        _flags["is_toplevel"] = True  # FIXME: Is this correct?
        self._debug("Getting toplevel for flags {}".format(str(_flags)))
        target = self._get_target(_flags)
        if target.toplevel:
            toplevel = self._parse_list(_flags, target.toplevel)
            self._debug(f"Matched toplevel {toplevel}")
            return " ".join(toplevel)
        else:
            s = "{} : Target '{}' has no toplevel"
            raise SyntaxError(s.format(self.name, target.name))

    def get_ttptttg(self, flags):
        self._debug("Getting ttptttg for flags {}".format(str(flags)))
        target = self._get_target(flags)
        ttptttg = []

        if not target:
            return ttptttg

        _ttptttg = []
        for f in target.generate:
            pf = f.name.parse(flags)
            # f.name might end up empty after parse. In that case, we ignore it
            if pf:
                _ttptttg.append({"name": pf, "params": f.params})

        if _ttptttg:
            self._debug(f" Matched generator instances {_ttptttg}")
        for gen in _ttptttg:
            gen_name = gen["name"]
            if not gen_name in self.generate:
                raise SyntaxError(
                    "Generator instance '{}', requested by target '{}', was not found".format(
                        gen_name, target.name
                    )
                )
            gen_inst = self.generate[gen_name]
            params = utils.merge_dict(gen_inst.parameters or {}, gen["params"])
            t = {
                "name": gen_name,
                "generator": str(gen_inst.generator),
                "config": dict(params),
                "pos": str(self.generate[gen_name].position or "append"),
            }
            ttptttg.append(t)
        return ttptttg

    def _get_vpi(self, flags):
        vpi = {}
        target = self._get_target(flags)
        if not target:
            return vpi
        for vpi_name in self._parse_list(flags, target.vpi):
            vpi_lib = self.vpi[vpi_name]
            files = []
            incfiles = []  # Really do this automatically?
            for fs in vpi_lib.filesets:
                for f in self.filesets[fs].files:
                    if f.is_include_file:
                        incfiles.append(f)
                    else:
                        files.append(f)
            vpi[vpi_name] = {
                "src_files": files,
                "inc_files": incfiles,
                "libs": [str(l) for l in vpi_lib.libs],
            }
        return vpi

    def get_vpi(self, flags):
        self._debug(f"Getting VPI libraries for flags {flags}")
        target = self._get_target(flags)
        vpi = []
        _vpi = self._get_vpi(flags)
        self._debug(" Matched VPI libraries {}".format([v for v in _vpi]))
        for k, v in sorted(_vpi.items()):
            vpi.append(
                {
                    "name": k,
                    "src_files": [f.name for f in v["src_files"]],
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

Targets:
{}"""
        if self.targets:
            l = max(len(x) for x in self.targets)
            targets = ""

            for t in sorted(self.targets):
                targets += "{} : {}\n".format(
                    t.ljust(l), self.targets[t].description or "<No description>"
                )
        else:
            targets = "<No targets>"
        return s.format(
            str(self.name),
            str(self.description or "<No description>"),
            str(self.core_root),
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

        target_name = None
        if flags.get("is_toplevel") and flags.get("target"):
            target_name = flags.get("target")
        else:
            target_name = "default"

        if target_name in self.targets:
            self._debug(f" Matched target {target_name}")
            return self.targets[target_name]
        else:
            self._debug("Matched no target")

    def _get_filesets(self, flags):
        self._debug("Getting filesets for flags '{}'".format(str(flags)))
        target = self._get_target(flags)
        if not target:
            return []
        filesets = []

        for fs in self._parse_list(flags, target.filesets):
            if not fs in self.filesets:
                raise SyntaxError(
                    "{} : Fileset '{}', requested by target '{}', was not found".format(
                        self.name, fs, target.name
                    )
                )
            filesets.append(self.filesets[fs])

        self._debug(f" Matched filesets {target.filesets}")
        return filesets

    def _parse_list(self, flags, l):
        r = []
        for x in l:
            _x = x.parse(flags)
            if _x:
                r.append(_x)
        return r

    # return [x.parse(flags) for x in l if x.parse(flags)]


description = """
---
Root:
  description : Root elements of the CAPI2 structure
  members:
    - name : name
      type : Vlnv
      desc : VLNV identifier for core
    - name : description
      type : String
      desc : Short description of core
    - name : provider
      type : Provider
      desc : Provider of core
    - name : CAPI=2
      type : String
      desc : Technically a header. Must appear as the first line in the core description file
  dicts:
    - name : filesets
      type : Fileset
      desc : File sets
    - name : generate
      type : Generate
      desc : Parametrized generator configurations
    - name : generators
      type : Generators
      desc : Generator provided by this core
    - name : scripts
      type : Script
      desc : Scripts that are used by the hooks
    - name : targets
      type : Target
      desc : Available targets
    - name : parameters
      type : Parameter
      desc : Available parameters
    - name : vpi
      type : Vpi
      desc : Available VPI modules
  lists:
    - name : virtual
      type : Vlnv
      desc : VLNV of a virtual core provided by this core. Versions are currently not supported, only the VLN part is used.

Fileset:
  description : A fileset represents a group of files with a common purpose. Each file in the fileset is required to have a file type and is allowed to have a logical_name which can be set for the whole fileset or individually for each file. A fileset can also have dependencies on other cores, specified in the depend section
  members:
    - name : file_type
      type : String
      desc : Default file_type for files in fileset
    - name : logical_name
      type : String
      desc : Default logical_name (i.e. library) for files in fileset
  lists:
    - name : files
      type : File
      desc : Files in fileset
    - name : depend
      type : StringWithUseFlags
      desc : Dependencies of fileset

Generate:
  description : The elements in this section each describe a parameterized instance of a generator. They specify which generator to invoke and any generator-specific parameters.
  members:
    - name : generator
      type : String
      desc : The generator to use. Note that the generator must be present in the dependencies of the core.
    - name : parameters
      type : Genparams
      desc : Generator-specific parameters. ``fusesoc gen show $generator`` might show available parameters
    - name : position
      type : String
      desc : Where to insert the generated core. Legal values are *first*, *append* or *last*. *append* will insert core after the core that called the generator

Generators:
  description : Generators are custom programs that generate FuseSoC cores. They are generally used during the build process, but can be used stand-alone too. This section allows a core to register a generator that can be used by other cores.
  members:
    - name : command
      type : String
      desc : The command to run (relative to the core root)
    - name : interpreter
      type : String
      desc : If the command needs a custom interpreter (such as python) this will be inserted as the first argument before command when calling the generator. The interpreter needs to be on the system PATH.
    - name : description
      type : String
      desc : Short description of the generator, as shown with ``fusesoc gen list``
    - name : usage
      type : String
      desc : A longer description of how to use the generator, including which parameters it uses (as shown with ``fusesoc gen show $generator``).

Target:
  description : A target is the entry point to a core. It describes a single use-case and what resources that are needed from the core such as file sets, generators, parameters and specific tool options. A core can have multiple targets, e.g. for simulation, synthesis or when used as a dependency for another core. When a core is used, only a single target is active. The *default* target is a special target that is always used when the core is being used as a dependency for another core or when no ``--target=`` flag is set.
  members:
    - name : default_tool
      type : String
      desc : Default tool to use unless overridden with ``--tool=``
    - name : description
      type : String
      desc : Description of the target
    - name : flow
      type : String
      desc : Edalize backend flow to use for target
    - name : flow_options
      type : Any
      desc : Tool- and flow-specific options
    - name : hooks
      type : Hooks
      desc : Script hooks to run when target is used
    - name : tools
      type : Tools
      desc : Tool-specific options for target
    - name : toplevel
      type : StringWithUseFlagsOrList
      desc : Top-level module. Normally a single module/entity but can be a list of several items
  lists:
    - name : filesets
      type : StringWithUseFlags
      desc : File sets to use in target
    - name : generate
      type : StringWithUseFlagsOrDict
      desc : Parameterized generators to run for this target with optional parametrization
    - name : parameters
      type : StringWithUseFlags
      desc : Parameters to use in target. The parameter default value can be set here with ``param=value``
    - name : vpi
      type : StringWithUseFlags
      desc : VPI modules to build and include for target
  dicts:
    - name : flags
      type : Any
      desc : Default values of flags

Tools:
  description : The valid subsections of the Tools section and their options are defined by what Edalize backends are available at runtime. The sections listed here are the ones that were available when the documentation was generated.
  members : []
Hooks:
  description : Hooks are scripts that are run at different points in the build process. They are always launched from the work root
  lists:
    - name : pre_build
      type : StringWithUseFlags
      desc : Scripts executed before the *build* phase
    - name : post_build
      type : StringWithUseFlags
      desc : Scripts executed after the *build* phase
    - name : pre_run
      type : StringWithUseFlags
      desc : Scrips executed before the *run* phase
    - name : post_run
      type : StringWithUseFlags
      desc : Scripts executed after the *run* phase

Parameter:
  description : A parameter is a compile-time or run-time configuration of a core.
  members:
    - name : datatype
      type : String
      desc : Parameter datatype. Legal values are *bool*, *file*, *int*, *str*. *file* is same as *str*, but prefixed with the current directory that FuseSoC runs from
    - name : default
      type : AnyType
      desc : Default value
    - name : description
      type : String
      desc : Description of the parameter, as can be seen with ``fusesoc run --target=$target $core --help``
    - name : paramtype
      type : StringWithUseFlags
      desc : Specifies type of parameter. Legal values are *cmdlinearg* for command-line arguments directly added when running the core, *generic* for VHDL generics, *plusarg* for verilog plusargs, *vlogdefine* for Verilog `` `define`` or *vlogparam* for verilog top-level parameters. All paramtypes are not valid for every backend. Consult the backend documentation for details.
    - name : scope
      type : String
      desc : "**Not used** : Kept for backwards compatibility"

Script:
  description : A script specifies how to run an external command that is called by the hooks section together with the actual files needed to run the script. Scripts are alway executed from the work root
  lists:
    - name : cmd
      type : String
      desc : List of command-line arguments
    - name : filesets
      type : String
      desc : Filesets needed to run the script
  dicts:
    - name : env
      type : String
      desc : Map of environment variables to set before launching the script

Vpi:
  description : A VPI (Verilog Procedural Interface) library is a shared object that is built and loaded by a simulator to provide extra Verilog system calls. This section describes what files and external libraries to use for building a VPI library
  lists:
    - name : libs
      type : String
      desc : External libraries to link against
    - name : filesets
      type : String
      desc : Filesets containing files to use when compiling the VPI library

"""


def _class_doc(items):
    s = items["description"] + "\n\n"
    lines = []
    name_len = 10
    type_len = 4
    for item in items.get("members", []):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]) + 3)
        lines.append((item["name"], "`" + item["type"] + "`_", item["desc"]))
    for item in items.get("dicts", []):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]) + 11)
        lines.append((item["name"], "Dict of `{}`_".format(item["type"]), item["desc"]))
    for item in items.get("lists", {}):
        name_len = max(name_len, len(item["name"]))
        type_len = max(type_len, len(item["type"]) + 11)
        lines.append((item["name"], "List of `{}`_".format(item["type"]), item["desc"]))

    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    s += "Field Name".ljust(name_len + 1) + "Type".ljust(type_len + 1) + "Description\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    for line in lines:
        s += line[0].ljust(name_len + 1)
        s += line[1].ljust(type_len + 1)
        s += line[2]
        s += "\n"
    s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
    return s


def _generate_classes(j, base_class):
    for cls, _items in j.items():
        class_members = {"__doc__": _class_doc(_items)}
        if "members" in _items:
            class_members["members"] = {}
            for key in _items["members"]:
                class_members[key["name"]] = None
                class_members["members"][key["name"]] = key["type"]
        if "lists" in _items:
            class_members["lists"] = {}
            for key in _items["lists"]:
                class_members[key["name"]] = []
                class_members["lists"][key["name"]] = key["type"]
                class_members[key["name"] + "_append"] = []
                class_members["lists"][key["name"] + "_append"] = key["type"]
        if "dicts" in _items:
            class_members["dicts"] = {}
            for key in _items["dicts"]:
                class_members[key["name"]] = {}
                class_members["dicts"][key["name"]] = key["type"]

        generatedClass = type(cls, (base_class,), class_members)
        globals()[generatedClass.__name__] = generatedClass


capi2_data = utils.yaml_read(description)

for backend in get_edatools():
    backend_name = backend.__name__
    if hasattr(backend, "get_doc"):
        if backend_name == "Edatool":
            continue
        tool_options = backend.get_doc(0)
    elif hasattr(backend, "tool_options"):
        _tool_options = getattr(backend, "tool_options")
        tool_options = {"description": f"Options for {backend_name} backend"}
        for group in ["members", "lists", "dicts"]:
            if group in _tool_options:
                tool_options[group] = []
                for _name, _type in _tool_options[group].items():
                    tool_options[group].append(
                        {"name": _name, "type": _type, "desc": ""}
                    )
    else:
        continue
    capi2_data["Tools"]["members"].append(
        {
            "name": backend_name.lower(),
            "type": backend_name,
            "desc": backend_name + "-specific options",
        }
    )
    capi2_data[backend_name] = tool_options

_generate_classes(capi2_data, Section)


def gen_doc():
    c = capi2_data.copy()
    s = """.. _ref_capi2:

***************
CAPI2 Reference
***************

CAPI2 (Core API version 2) describes the properties of a core as a YAML data structure.

Types
-----

File
~~~~
A File object represents a physical file. It can be a simple string, with the path to the file relative to the core root (e.g. *path/to/file.v*). It is also possible to assign attributes to a file, by using the file name as a dictionary key and the attributes as a map. (e.g. *path/to/file.v : {is_include_file : true, file_type : systemVerilogSource}*). Valid attributes are

=============== ==== ===========
Attribute       Type Description
=============== ==== ===========
is_include_file bool Treats file as an include file when true
include_path    str  Explicitly set an include directory, relative to core root, instead of the directory containing the file
file_type       str  File type. Overrides the file_type set on the containing fileset
logical_name    str  Logical name, i.e. library for VHDL/SystemVerilog. Overrides the logical_name set on the containing fileset
copyto          str  Copy the source file to this path in the work directory.
=============== ==== ===========

Genparams
~~~~~~~~~
Genparams are private configuration for a generator. Normally specified as a map of key/value pairs

Provider
~~~~~~~~
Specifies how to fetch the core. The presence of a provider section indicates this is a remote core that has its source code separated from the core description file.

String
~~~~~~

String is an unparsed (plain) string.

StringWithUseFlags
~~~~~~~~~~~~~~~~~~

StringWithUseFlags is a string that can contain CAPI2 expressions that are evaluated during parsing.

CAPI2 expressions return a value depending on a :ref:`flag <ug_build_system_flags>` being set or not.

* To test if a flag is set (true) and return ``my_string`` in that case, use the expression ``my_flag ? (my_string)``.
* To test if a flag is not set (false) and return ``my_string`` in that case, use the expression ``!my_flag ? (my_string)``.

.. note::
   **Quotation marks are required** for strings starting with an exclamation mark (``!``), but :ref:`always recommended <ug_build_system_core_files_yaml_intro>`.

Refer to the section :ref:`ug_build_system_flags` in the User Guide for more information on flags.

StringWithUseFlagsOrDict
~~~~~~~~~~~~~~~~~~~~~~~~

Item is allowed to be either a `StringWithUseFlags`_ or a dict of `StringWithUseFlags`_.

StringWithUseFlagsOrList
~~~~~~~~~~~~~~~~~~~~~~~~

Item is allowed to be either a `StringWithUseFlags`_ or a list of `StringWithUseFlags`_

Vlnv
~~~~~~
:-separated VLNV (Vendor, Library, Name, Version) identifier

Dict
~~~~

A dictionary.

Bool
~~~~

A boolean.

Integer
~~~~~~~

An integer.

List
~~~~

All keys that are defined as lists have a corresponding *<key>_append* key. The items in the *<key>_append* list is automatically appended to the list of the original key.

**Example** A target contains the following keys

::

    filesets : [fileset_a, fileset_b]
    filesets_append : [fileset_c, fileset_d]

This will be evaluated to

::

    filesets : [fileset_a, fileset_b, fileset_c, fileset_d]

The main use case for this feature is inheritance between targets with yaml anchors as in the following example where a board-specific implementation and a simulation target inherits from the default target

::

    targets:
      default: &base
        filesets: [core]

      myboard:
        <<: *base
        filesets_append: [myboard_files]

      sim:
        <<: *base
        filesets_append: [testbench]

Sections
--------

 The first table lists all valid keywords in the document root while the other tables are keywords for subsections of the tree

"""

    def print_class(items):
        s = items["description"] + "\n\n"
        lines = []
        name_len = 10
        type_len = 4
        for item in items.get("members", []):
            name_len = max(name_len, len(item["name"]))
            type_len = max(type_len, len(item["type"]) + 3)
            lines.append((item["name"], "`" + item["type"] + "`_", item["desc"]))
        for item in items.get("dicts", []):
            name_len = max(name_len, len(item["name"]))
            type_len = max(type_len, len(item["type"]) + 11)
            lines.append(
                (item["name"], "Dict of `{}`_".format(item["type"]), item["desc"])
            )
        for item in items.get("lists", {}):
            name_len = max(name_len, len(item["name"]))
            type_len = max(type_len, len(item["type"]) + 11)
            lines.append(
                (item["name"], "List of `{}`_".format(item["type"]), item["desc"])
            )

        s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
        s += (
            "Field Name".ljust(name_len + 1)
            + "Type".ljust(type_len + 1)
            + "Description\n"
        )
        s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
        for line in lines:
            s += line[0].ljust(name_len + 1)
            s += line[1].ljust(type_len + 1)
            s += line[2]
            s += "\n"
        s += "=" * name_len + " " + "=" * type_len + " " + "=" * 11 + "\n"
        return s

    s += _class_doc(c.pop("Root"))
    for k, v in c.items():
        s += "\n{}\n{}\n\n".format(k, "~" * len(k))
        s += _class_doc(v)

    return s
