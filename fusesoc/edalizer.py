# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import hashlib
import logging
import os
import pathlib
import shutil
from filecmp import cmp
from importlib import import_module

from fusesoc import utils
from fusesoc.capi2.coreparser import Core2Parser
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


def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif v.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


class Edalizer:
    def __init__(
        self,
        toplevel,
        flags,
        work_root,
        core_manager,
        export_root=None,
        system_name=None,
        resolve_env_vars=False,
    ):
        logger.debug("Building EDAM structure")

        self.toplevel = toplevel
        self.flags = flags
        self.core_manager = core_manager
        self.work_root = work_root
        self.export_root = export_root
        self.system_name = system_name
        self.resolve_env_vars = resolve_env_vars

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
        """Get a list of all "used" cores after the dependency resolution"""
        return self.core_manager.get_depends(self.toplevel, self.flags)

    @property
    def discovered_cores(self):
        """Get a list of all cores found by fusesoc"""
        return self.core_manager.db.find()

    def apply_filters(self, global_filters):
        filters = self.edam.get("filters", []) + global_filters
        for f in filters:
            try:
                filter_class = getattr(
                    import_module(f"fusesoc.filters.{f}"), f.capitalize()
                )
                logger.info(f"Applying filter {f}")
                self.edam = filter_class().run(self.edam, self.work_root)
            except ModuleNotFoundError:
                raise RuntimeError(f"Could not find EDAM filter '{f}'")
            except Exception as e:
                raise RuntimeError(f"Filter error: {str(e)}")
            except SystemExit as e:
                raise RuntimeError(f"Filter exited with error code {str(e)}")

    def run(self):
        """Run all steps to create a EDAM file"""

        # Run the setup task on all cores (fetch and patch them as needed)
        self.setup_cores()

        # Get all generators defined in any of the cores
        self.extract_generators()

        # Run all generators. Generators can create new cores, which are added
        # to the list of available cores.
        self.run_generators()

        # Create EDAM file contents
        self.create_edam()

        # Write lockfile if appropriate
        self.core_manager.db.store_lockfile(self.cores)

        return self.edam

    def _core_flags(self, core):
        """Get flags for a specific core"""

        core_flags = self.flags.copy()
        core_flags["is_toplevel"] = core.name == self.toplevel
        return core_flags

    def setup_cores(self):
        """Setup cores: fetch resources, patch them, etc."""
        for core in self.cores:
            logger.info("Preparing " + str(core.name))
            core.setup()

    def extract_generators(self):
        """Get all registered generators from the cores"""
        generators = {}
        for core in self.cores:
            _flags = self._core_flags(core)
            logger.debug("Searching for generators in " + str(core.name))
            core_generators = core.get_generators(_flags)
            logger.debug(f"Found generators: {core_generators.keys()}")
            generators.update(core_generators)

        self.generators = generators

    def run_generators(self):
        """Run all generators"""
        self._resolved_or_generated_cores = []
        for core in self.cores:
            logger.debug("Running generators in " + str(core.name))
            core_flags = self._core_flags(core)
            self._resolved_or_generated_cores.append(core)
            for ttptttg_data in core.get_ttptttg(core_flags):
                _ttptttg = Ttptttg(
                    ttptttg_data,
                    core,
                    self.generators,
                    self.work_root,
                    resolve_env_vars=self.resolve_env_vars,
                )
                try:
                    gen_cores = _ttptttg.generate()
                except RuntimeError as e:
                    logger.error(e)
                    raise RuntimeError(
                        f"Failed to run generator '{ttptttg_data['name']}'"
                    )
                    gen_cores = []
                for gen_core in gen_cores:
                    core.direct_deps.append(str(gen_core.name))
                    gen_core.pos = _ttptttg.pos
                    self._resolved_or_generated_cores.append(gen_core)

    def export(self):
        for core in self.cores:
            _flags = self._core_flags(core)

            # Export core files
            if self.export_root:
                files_root = os.path.join(self.export_root, core.name.sanitized_name)
                core.export(files_root, _flags)
            else:
                files_root = core.files_root

            # Add copyto files
            for file in core.get_files(_flags):
                if file.get("copyto"):
                    src = os.path.join(files_root, file["name"])
                    self._copyto(src, file.get("copyto"))

    def _copyto(self, src, name):
        dst = os.path.join(self.work_root, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)

        if not os.path.exists(dst) or not cmp(src, dst):
            try:
                shutil.copy2(src, dst)
            except IsADirectoryError:
                shutil.copytree(
                    src,
                    dst,
                    dirs_exist_ok=True,
                )

    def create_edam(self):
        first_snippets = []
        snippets = []
        last_snippets = []
        parameters = {}
        for core in self.cores:
            snippet = {}

            logger.debug("Collecting EDAM parameters from {}".format(str(core.name)))
            _flags = self._core_flags(core)

            # Extract direct dependencies
            snippet["dependencies"] = {str(core.name): core.direct_deps}

            # Extract files
            if self.export_root:
                files_root = os.path.join(self.export_root, core.name.sanitized_name)
            else:
                files_root = core.files_root

            rel_root = os.path.relpath(files_root, self.work_root)

            # Extract core description file
            snippet["cores"] = {
                str(core.name): {
                    "core_file": os.path.relpath(core.core_file, self.work_root),
                    "dependencies": core.direct_deps,
                }
            }

            # Extract parameters
            snippet["parameters"] = core.get_parameters(_flags, parameters)
            merge_dict(parameters, snippet["parameters"])

            # Extract tool options
            if self.flags.get("tool"):
                snippet["tool_options"] = {
                    self.flags["tool"]: core.get_tool_options(_flags)
                }

            # Extract EDAM filters
            snippet["filters"] = core.get_filters(_flags)

            # Extract flow options
            snippet["flow_options"] = core.get_flow_options(_flags)

            # Extract scripts
            snippet["hooks"] = core.get_scripts(rel_root, _flags)

            _files = []
            for file in core.get_files(_flags):

                # Reparent file path
                file["name"] = str(
                    file.get("copyto", os.path.join(rel_root, file["name"]))
                )

                # Set owning core
                file["core"] = str(core.name)

                # copyto tag shouldn't be in EDAM
                file.pop("copyto", None)

                # Reparent include paths
                if file.get("include_path"):
                    file["include_path"] = os.path.join(rel_root, file["include_path"])

                _files.append(file)

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
                elif core.pos == "prepend" and len(snippets) > 0:
                    snippets.insert(len(snippets) - 1, snippet)
                else:
                    snippets.append(snippet)
            else:
                snippets.append(snippet)

        top_core = self.resolved_cores[-1]
        self.edam = {
            "version": "0.2.1",
            "name": self.system_name or top_core.name.sanitized_name,
            "toplevel": top_core.get_toplevel(self.flags),
        }

        for snippet in first_snippets + snippets + last_snippets:
            merge_dict(self.edam, snippet)

    def _build_parser(self, backend_class, edam):
        typedict = {
            "bool": {"type": str2bool, "nargs": "?", "const": True},
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
                logging.warning(
                    "Parameter '{}' has unsupported type '{}' for requested backend".format(
                        name, _paramtype
                    )
                )

        # backend_args.
        backend_args = parser.add_argument_group("Backend arguments")

        if hasattr(backend_class, "get_flow_options"):
            for k, v in backend_class.get_flow_options().items():
                backend_args.add_argument(
                    "--" + k,
                    help=v["desc"],
                    **typedict[v["type"]],
                )
            for k, v in backend_class.get_tool_options(
                self.activated_flow_options
            ).items():
                backend_args.add_argument(
                    "--" + k,
                    help=v["desc"],
                    **typedict[v["type"]],
                )
        else:
            _opts = backend_class.get_doc(0)
            for _opt in _opts.get("members", []) + _opts.get("lists", []):
                backend_args.add_argument("--" + _opt["name"], help=_opt["desc"])

        return parser

    def add_parsed_args(self, backend_class, parsed_args):
        if hasattr(backend_class, "get_flow_options"):
            backend_members = []
            backend_lists = []
            for k, v in backend_class.get_flow_options().items():
                if v.get("list"):
                    backend_lists.append(k)
                else:
                    backend_members.append(k)
            for k, v in backend_class.get_tool_options(
                self.activated_flow_options
            ).items():
                if v.get("list"):
                    backend_lists.append(k)
                else:
                    backend_members.append(k)
            tool_options = self.edam["flow_options"]
        else:
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

    def _parse_flow_options(self, backend_class, backendargs, edam):
        available_flow_options = backend_class.get_flow_options()

        # First we check which flow options that are set in the EDAM.
        # edam["flow_options"] contain both flow and tool options, so
        # we only pick the former here
        flow_options = {}
        for k, v in edam["flow_options"].items():
            if k in available_flow_options:
                flow_options[k] = v

        # Next we build a parser and use it to parse the command-line
        progname = "fusesoc run {}".format(edam["name"])
        parser = argparse.ArgumentParser(
            prog=progname, conflict_handler="resolve", add_help=False
        )
        backend_args = parser.add_argument_group("Flow options")
        typedict = {
            "bool": {"type": str2bool, "nargs": "?", "const": True},
            "file": {"type": str, "nargs": 1, "action": FileAction},
            "int": {"type": int, "nargs": 1},
            "str": {"type": str, "nargs": 1},
            "real": {"type": float, "nargs": 1},
        }
        for k, v in available_flow_options.items():
            backend_args.add_argument(
                "--" + k,
                help=v["desc"],
                **typedict[v["type"]],
            )

        # Parse known args (i.e. only flow options) from the command-line
        parsed_args = parser.parse_known_args(backendargs)[0]

        # Clean up parsed arguments object and convert to dict
        parsed_args_dict = {}
        for key, value in sorted(vars(parsed_args).items()):
            # Remove arguments with value None, i.e. arguments not encountered
            # on the command line
            if value is None:
                continue
            _value = value[0] if type(value) == list else value

            # If flow option is a list, we split up the parsed string
            if "list" in available_flow_options[key]:
                _value = _value.split(" ")
            parsed_args_dict[key] = _value

        # Add parsed args to the ones from the EDAM
        merge_dict(flow_options, parsed_args_dict)

        return flow_options

    def parse_args(self, backend_class, backendargs):
        # First we need to see which flow options are set,
        # in order to know which tool options that are relevant
        # for this configuration of the flow
        if hasattr(backend_class, "get_flow_options"):
            self.activated_flow_options = self._parse_flow_options(
                backend_class, backendargs, self.edam
            )

        parser = self._build_parser(backend_class, self.edam)
        parsed_args = parser.parse_args(backendargs)

        args_dict = {}
        for key, value in sorted(vars(parsed_args).items()):
            if value is None:
                continue
            _value = value[0] if type(value) == list else value
            args_dict[key] = _value

        self.add_parsed_args(backend_class, args_dict)

    def to_yaml(self, edam_file):
        pathlib.Path(edam_file).parent.mkdir(parents=True, exist_ok=True)
        return utils.yaml_fwrite(edam_file, self.edam)


from fusesoc.core import Core
from fusesoc.utils import Launcher


class Ttptttg:
    def __init__(self, ttptttg, core, generators, work_root, resolve_env_vars=False):
        generator_name = ttptttg["generator"]
        if not generator_name in generators:
            raise RuntimeError(
                "Could not find generator '{}' requested by {}".format(
                    generator_name, core.name
                )
            )
        self.core = core
        self.generator = generators[generator_name]
        self.name = ttptttg["name"]
        self.pos = ttptttg["pos"]
        self.gen_name = generator_name
        self.gen_root = self.core.cache_root if self.is_cacheable() else work_root
        self.resolve_env_vars = resolve_env_vars
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

    def _sha256_input_yaml_hexdigest(self):
        data = self.generator_input.copy()
        # Remove files_root since that is not deterministic
        data.pop("files_root")
        return hashlib.sha256(utils.yaml_dump(data).encode()).hexdigest()

    def _sha256_file_input_hexdigest(self):
        input_files = []
        logger.debug(
            "Configured file_input_parameters: "
            + self.generator["file_input_parameters"]
        )
        for param in self.generator["file_input_parameters"].split():
            try:
                input_files.append(self.generator_input["parameters"][param])
            except KeyError:
                logger.debug(
                    f"Parameter {param} does not exist in parameters. File input will not be included in file input hash calculation."
                )

        logger.debug("Found input files: " + str(input_files))

        hash = hashlib.sha256()

        for f in input_files:
            if type(f) == list:
                files = f
            else:
                files = [f]
            for ff in files:
                abs_f = os.path.join(self.generator_input["files_root"], ff)
                try:
                    hash.update(pathlib.Path(abs_f).read_bytes())
                except Exception as e:
                    raise RuntimeError("Unable to hash file: " + str(e))

        return hash.hexdigest()

    def _run(self, generator_cwd):
        logger.info("Generating " + str(self.vlnv))

        generator_input_file = os.path.join(generator_cwd, self.name + "_input.yml")

        pathlib.Path(generator_cwd).mkdir(parents=True, exist_ok=True)
        utils.yaml_fwrite(generator_input_file, self.generator_input)

        args = [
            os.path.join(
                os.path.abspath(self.generator["root"]), self.generator["command"]
            ),
            os.path.abspath(generator_input_file),
        ]

        if "interpreter" in self.generator:
            interp = self.generator["interpreter"]
            interppath = shutil.which(interp)
            if not interppath:
                raise RuntimeError(
                    f"Could not find generator interpreter '{interp}' using shutil.which.\n"
                    f"Interpreter requested by generator {self.gen_name}, requested by core {self.core}.\n"
                )
            args[0:0] = [interppath]

        Launcher(args[0], args[1:], cwd=generator_cwd).run()

    def is_input_cacheable(self):
        return (
            "cache_type" in self.generator and self.generator["cache_type"] == "input"
        )

    def is_generator_cacheable(self):
        return (
            "cache_type" in self.generator
            and self.generator["cache_type"] == "generator"
        )

    def is_cacheable(self):
        return self.is_input_cacheable() or self.is_generator_cacheable()

    def acquire_cache_lock(self):
        have_lock = False
        # while not have_lock:
        #    if

    def generate(self):
        """Run a parametrized generator

        Returns:
            list: Cores created by the generator
        """

        hexdigest = self._sha256_input_yaml_hexdigest()

        logger.debug("Generator parameters hash: " + hexdigest)

        generator_cwd = os.path.join(
            self.gen_root,
            "generator_cache",
            self.vlnv.sanitized_name + "-" + hexdigest,
        )

        if "file_input_parameters" in self.generator:
            # If file_input_parameters has been configured in the generator
            # parameters will be iterated to look for files to add to the
            # input files hash calculation.
            file_input_hash = self._sha256_file_input_hexdigest()
            generator_cwd = os.path.join(generator_cwd, file_input_hash)
            logger.debug("Generator input files hash: " + file_input_hash)

        logger.debug("Generator cwd: " + generator_cwd)

        if os.path.lexists(generator_cwd) and not os.path.isdir(generator_cwd):
            raise RuntimeError(
                "Unable to create generator working directory since it already exists and is not a directory: "
                + generator_cwd
                + "\n"
                + "Remove it manually or run 'fusesoc gen clean'"
            )

        if self.is_input_cacheable() and os.path.isdir(generator_cwd):
            logger.info("Found cached output for " + str(self.vlnv))
        else:
            # TODO: Acquire a lock here to ensure that we are the only users
            if self.is_generator_cacheable():
                logger.warning(
                    "Support for generator-side cachable cores are deprecated and will be removed"
                )
            else:
                shutil.rmtree(generator_cwd, ignore_errors=True)
            try:
                self._run(generator_cwd)
            except:
                # If the generator invocation failed for any reason, its output
                # directory is removed. While this is bad for debugging failing
                # generators, it at least prevents the next FuseSoC-run to
                # assume, that the generator was successful and hence a failed
                # generator is retried on the next FuseSoC-run.
                logger.debug("Generator failed, removing its output files")
                shutil.rmtree(generator_cwd, ignore_errors=False)
                raise
            # TODO: Release cache lock

        cores = []
        logger.debug("Looking for generated or cached cores in " + generator_cwd)
        parser = Core2Parser(self.resolve_env_vars, allow_additional_properties=False)
        for root, dirs, files in os.walk(generator_cwd):
            for f in files:
                if f.endswith(".core"):
                    try:
                        cores.append(
                            Core(
                                parser,
                                os.path.join(root, f),
                                generated=True,
                            )
                        )
                    except SyntaxError as e:
                        w = "Failed to parse generated core file " + f + ": " + e.msg
                        raise RuntimeError(w)
        logger.debug("Found " + ", ".join(str(c.name) for c in cores))
        return cores
