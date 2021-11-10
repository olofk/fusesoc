# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import logging
import os
import shutil
import tempfile

from fusesoc import utils
from fusesoc.coremanager import DependencyError
from fusesoc.utils import merge_dict
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.expandvars(values[0])
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        setattr(namespace, self.dest, [path])


class Edalizer:
    def __init__(
        self,
        toplevel,
        flags,
        work_root,
        core_manager,
        export_root=None,
        system_name=None,
    ):
        logger.debug("Building EDA API")

        self.toplevel = toplevel
        self.flags = flags
        self.core_manager = core_manager
        self.work_root = work_root
        self.export_root = export_root
        self.system_name = system_name

        self.generators = {}

        self._resolved_or_generated_cores = []

    @property
    def cores(self):
        if self._resolved_or_generated_cores:
            return self._resolved_or_generated_cores
        else:
            return self.resolved_cores

    @property
    def resolved_cores(self):
        """ Get a list of all "used" cores after the dependency resolution """
        try:
            return self.core_manager.get_depends(self.toplevel, self.flags)
        except DependencyError as e:
            logger.error(
                e.msg + f"\nFailed to resolve dependencies for {self.toplevel}"
            )
            exit(1)
        except SyntaxError as e:
            logger.error(e.msg)
            exit(1)

    @property
    def discovered_cores(self):
        """ Get a list of all cores found by fusesoc """
        return self.core_manager.db.find()

    def run(self):
        """ Run all steps to create a EDAM file """

        # Run the setup task on all cores (fetch and patch them as needed)
        self.setup_cores()

        # Get all generators defined in any of the cores
        self.extract_generators()

        # Run all generators. Generators can create new cores, which are added
        # to the list of available cores.
        self.run_generators()

        # Create EDA API file contents
        self.create_edam()
        return self.edam

    def _core_flags(self, core):
        """ Get flags for a specific core """

        core_flags = self.flags.copy()
        core_flags["is_toplevel"] = core.name == self.toplevel
        return core_flags

    def setup_cores(self):
        """ Setup cores: fetch resources, patch them, etc. """
        for core in self.cores:
            logger.info("Preparing " + str(core.name))
            core.setup()

    def extract_generators(self):
        """ Get all registered generators from the cores """
        generators = {}
        for core in self.cores:
            logger.debug("Searching for generators in " + str(core.name))
            if hasattr(core, "get_generators"):
                core_generators = core.get_generators()
                if core_generators:
                    logger.debug(f"Found generators: {core_generators.keys()}")
                generators.update(core_generators)

        self.generators = generators

    def run_generators(self):
        """ Run all generators """
        self._resolved_or_generated_cores = []
        for core in self.cores:
            logger.debug("Running generators in " + str(core.name))
            core_flags = self._core_flags(core)
            self._resolved_or_generated_cores.append(core)
            if hasattr(core, "get_ttptttg"):
                for ttptttg_data in core.get_ttptttg(core_flags):
                    _ttptttg = Ttptttg(
                        ttptttg_data,
                        core,
                        self.generators,
                    )
                    for gen_core in _ttptttg.generate():
                        gen_core.pos = _ttptttg.pos
                        self._resolved_or_generated_cores.append(gen_core)

    def create_edam(self):
        first_snippets = []
        snippets = []
        last_snippets = []
        parameters = {}
        for core in self.cores:
            snippet = {}

            logger.debug("Collecting EDA API parameters from {}".format(str(core.name)))
            _flags = self._core_flags(core)

            # Extract direct dependencies
            snippet["dependencies"] = {str(core.name): core.direct_deps}

            # Extract files
            if self.export_root:
                files_root = os.path.join(self.export_root, core.sanitized_name)
                core.export(files_root, _flags)
            else:
                files_root = core.files_root

            rel_root = os.path.relpath(files_root, self.work_root)

            # Extract parameters
            snippet["parameters"] = core.get_parameters(_flags, parameters)
            merge_dict(parameters, snippet["parameters"])

            # Extract tool options
            snippet["tool_options"] = {
                self.flags["tool"]: core.get_tool_options(_flags)
            }

            # Extract scripts
            snippet["hooks"] = core.get_scripts(rel_root, _flags)

            _files = []
            for file in core.get_files(_flags):
                _f = file
                if file.get("copyto"):
                    _name = file["copyto"]
                    dst = os.path.join(self.work_root, _name)
                    _dstdir = os.path.dirname(dst)
                    if not os.path.exists(_dstdir):
                        os.makedirs(_dstdir)
                    try:
                        shutil.copy2(os.path.join(files_root, file["name"]), dst)
                    except IsADirectoryError:
                        shutil.copytree(
                            os.path.join(files_root, file["name"]),
                            dst,
                            dirs_exist_ok=True,
                        )
                    del _f["copyto"]
                else:
                    _name = os.path.join(rel_root, file["name"])
                _f["name"] = str(_name)
                _f["core"] = str(core.name)
                if file.get("include_path"):
                    _f["include_path"] = os.path.join(rel_root, file["include_path"])

                _files.append(_f)

            snippet["files"] = _files

            # Extract VPI modules
            snippet["vpi"] = []
            for _vpi in core.get_vpi(_flags):
                snippet["vpi"].append(
                    {
                        "name": _vpi["name"],
                        "src_files": [
                            os.path.join(rel_root, f) for f in _vpi["src_files"]
                        ],
                        "include_dirs": [
                            os.path.join(rel_root, i) for i in _vpi["include_dirs"]
                        ],
                        "libs": _vpi["libs"],
                    }
                )

            if hasattr(core, "pos"):
                if core.pos == "first":
                    first_snippets.append(snippet)
                elif core.pos == "last":
                    last_snippets.append(snippet)
                else:
                    snippets.append(snippet)
            else:
                snippets.append(snippet)

        top_core = self.resolved_cores[-1]
        self.edam = {
            "version": "0.2.1",
            "dependencies": {},
            "files": [],
            "hooks": {},
            "name": self.system_name or top_core.sanitized_name,
            "parameters": {},
            "tool_options": {},
            "toplevel": top_core.get_toplevel(self.flags),
            "top_core": top_core.core_file,
            "vpi": [],
        }

        for snippet in first_snippets + snippets + last_snippets:
            merge_dict(self.edam, snippet)

    def _build_parser(self, backend_class, edam):
        typedict = {
            "bool": {"action": "store_true"},
            "file": {"type": str, "nargs": 1, "action": FileAction},
            "int": {"type": int, "nargs": 1},
            "str": {"type": str, "nargs": 1},
            "real": {"type": float, "nargs": 1},
        }
        progname = "fusesoc run {}".format(edam["name"])

        parser = argparse.ArgumentParser(prog=progname, conflict_handler="resolve")
        param_groups = {}
        _descr = {
            "plusarg": "Verilog plusargs (Run-time option)",
            "vlogparam": "Verilog parameters (Compile-time option)",
            "vlogdefine": "Verilog defines (Compile-time global symbol)",
            "generic": "VHDL generic (Run-time option)",
            "cmdlinearg": "Command-line arguments (Run-time option)",
        }
        param_type_map = {}

        paramtypes = backend_class.argtypes
        for name, param in edam["parameters"].items():
            _description = param.get("description", "No description")
            _paramtype = param["paramtype"]
            if _paramtype in paramtypes:
                if not _paramtype in param_groups:
                    param_groups[_paramtype] = parser.add_argument_group(
                        _descr[_paramtype]
                    )

                default = None
                if not param.get("default") is None:
                    try:
                        if param["datatype"] == "bool":
                            default = param["default"]
                        else:
                            default = [
                                typedict[param["datatype"]]["type"](param["default"])
                            ]
                    except KeyError as e:
                        pass
                try:
                    param_groups[_paramtype].add_argument(
                        "--" + name,
                        help=_description,
                        default=default,
                        **typedict[param["datatype"]],
                    )
                except KeyError as e:
                    raise RuntimeError(
                        "Invalid data type {} for parameter '{}'".format(str(e), name)
                    )
                param_type_map[name.replace("-", "_")] = _paramtype
            else:
                logging.warn(
                    "Parameter '{}' has unsupported type '{}' for requested backend".format(
                        name, _paramtype
                    )
                )

        # backend_args.
        backend_args = parser.add_argument_group("Backend arguments")
        _opts = backend_class.get_doc(0)

        for _opt in _opts.get("members", []) + _opts.get("lists", []):
            backend_args.add_argument("--" + _opt["name"], help=_opt["desc"])
        return parser

    def add_parsed_args(self, backend_class, parsed_args):
        _opts = backend_class.get_doc(0)
        # Parse arguments
        backend_members = [x["name"] for x in _opts.get("members", [])]
        backend_lists = [x["name"] for x in _opts.get("lists", [])]

        tool = backend_class.__name__.lower()
        tool_options = self.edam["tool_options"][tool]

        for key, value in sorted(parsed_args.items()):
            if value is None:
                pass
            elif key in backend_members:
                tool_options[key] = value
            elif key in backend_lists:
                if not key in tool_options:
                    tool_options[key] = []
                tool_options[key] += value.split(" ")
            elif key in self.edam["parameters"]:
                _param = self.edam["parameters"][key]
                _param["default"] = value
            else:
                raise RuntimeError("Unknown parameter " + key)

    def parse_args(self, backend_class, backendargs, edam):
        parser = self._build_parser(backend_class, edam)
        parsed_args = parser.parse_args(backendargs)

        args_dict = {}
        for key, value in sorted(vars(parsed_args).items()):
            if value is None:
                continue
            _value = value[0] if type(value) == list else value
            args_dict[key] = _value
        return args_dict

    def to_yaml(self, edam_file):
        return utils.yaml_fwrite(edam_file, self.edam)


from fusesoc.core import Core
from fusesoc.utils import Launcher


class Ttptttg:
    def __init__(self, ttptttg, core, generators):
        generator_name = ttptttg["generator"]
        if not generator_name in generators:
            raise RuntimeError(
                "Could not find generator '{}' requested by {}".format(
                    generator_name, core.name
                )
            )
        self.generator = generators[generator_name]
        self.name = ttptttg["name"]
        self.pos = ttptttg["pos"]
        parameters = ttptttg["config"]

        vlnv_str = ":".join(
            [
                core.name.vendor,
                core.name.library,
                core.name.name + "-" + self.name,
                core.name.version,
            ]
        )
        self.vlnv = Vlnv(vlnv_str)

        self.generator_input = {
            "files_root": os.path.abspath(core.files_root),
            "gapi": "1.0",
            "parameters": parameters,
            "vlnv": vlnv_str,
        }

    def generate(self):
        """Run a parametrized generator

        Returns:
            list: Cores created by the generator
        """
        generator_cwd = os.path.join(tempfile.mkdtemp(prefix=self.vlnv.sanitized_name))
        generator_input_file = os.path.join(generator_cwd, self.name + "_input.yml")

        logger.info("Generating " + str(self.vlnv))
        utils.yaml_fwrite(generator_input_file, self.generator_input)

        args = [
            os.path.join(os.path.abspath(self.generator.root), self.generator.command),
            os.path.abspath(generator_input_file),
        ]

        if self.generator.interpreter:
            args[0:0] = [self.generator.interpreter]

        Launcher(args[0], args[1:], cwd=generator_cwd).run()

        cores = []
        logger.debug("Looking for generated cores in " + generator_cwd)
        for root, dirs, files in os.walk(generator_cwd):
            for f in files:
                if f.endswith(".core"):
                    try:
                        cores.append(Core(os.path.join(root, f)))
                    except SyntaxError as e:
                        w = "Failed to parse generated core file " + f + ": " + e.msg
                        raise RuntimeError(w)
        logger.debug("Found " + ", ".join(str(c.name) for c in cores))
        return cores
