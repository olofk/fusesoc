# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import logging
import os
import shutil

from fusesoc import utils
from fusesoc.coremanager import DependencyError
from fusesoc.librarymanager import Library
from fusesoc.utils import depgraph_cores, depgraph_to_dot, merge_dict
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

        # A dictionary of generators. This is keyed by the generator name and
        # values are pairs (core_name, gen) where core_name is the name of the
        # core that produced the generator and gen is a Generator object.
        self.generators = {}
        self._cached_core_list_for_generator = []

        # A set of names of cores that have VPI information. Populated in
        # create_eda_api_struct.
        self._cores_with_vpi = set()

    @property
    def cores(self):
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
        """ Run all steps to create a EDA API YAML file """

        # Clean out old work root
        self._prepare_work_root()

        # Run the setup task on all cores (fetch and patch them as needed)
        self.setup_cores()

        # Get all generators defined in any of the cores
        self.extract_generators()

        # Run all generators. Generators can create new cores, which are added
        # to the list of available cores.
        self.run_generators()

        # Dump complete dependency tree as dot file.
        core_graph = self.core_manager.get_dependency_graph(self.toplevel, self.flags)
        dot_filepath = os.path.join(
            self.work_root, self.toplevel.sanitized_name + ".deps-after-generators.dot"
        )
        with open(dot_filepath, "w") as f:
            f.write(depgraph_to_dot(core_graph))
        logger.info("Wrote dependency graph to {}".format(dot_filepath))

        # Create EDA API file contents
        self.create_eda_api_struct()

        # Dump flattened dependency tree as Makefile fragment (this has to come
        # after create_eda_api_struct, because we need _cores_with_vpi)
        mk_filepath = os.path.join(self.work_root, "core-deps.mk")
        mk_contents = self._depgraph_to_mk(core_graph)
        if mk_contents is not None:
            with open(mk_filepath, "w") as f:
                f.write(mk_contents)
            logger.info("Wrote Makefile fragment to {}".format(mk_filepath))

    def _core_flags(self, core):
        """ Get flags for a specific core """

        core_flags = self.flags.copy()
        core_flags["is_toplevel"] = core.name == self.toplevel
        return core_flags

    def _prepare_work_root(self):
        if os.path.exists(self.work_root):
            for f in os.listdir(self.work_root):
                if os.path.isdir(os.path.join(self.work_root, f)):
                    shutil.rmtree(os.path.join(self.work_root, f))
                else:
                    os.remove(os.path.join(self.work_root, f))
        else:
            os.makedirs(self.work_root)

        # Prevent fusesoc from picking up core files generated in work_root
        # without explicitly adding them to the library, as generators do.
        with open(os.path.join(self.work_root, "FUSESOC_IGNORE"), "w") as f:
            f.write(
                "FuseSoC ignores this directory and all subdirectories\n"
                "when searching for core files.\n"
            )

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
                for gen_name, generator in core.get_generators().items():
                    logger.debug("  Found generator: {}".format(gen_name))
                    generators[gen_name] = (core.name, generator)

        self.generators = generators

    def _invalidate_cached_core_list_for_generator(self):
        if self._cached_core_list_for_generator:
            self._cached_core_list_for_generator = None

    def _core_list_for_generator(self):
        """Produce a dictionary of cores, suitable for passing to a generator

        The results of this functions are cached for a significant overall
        speedup. Users need to call _invalidate_cached_core_list_for_generator()
        whenever the CoreDB is modified.
        """

        if self._cached_core_list_for_generator:
            return self._cached_core_list_for_generator

        out = {}
        resolved_cores = self.resolved_cores  # cache for speed
        for core in self.discovered_cores:
            core_flags = self._core_flags(core)
            out[str(core)] = {
                "capi_version": core.capi_version,
                "core_filepath": os.path.abspath(core.core_file),
                "used": core in resolved_cores,
                "core_root": os.path.abspath(core.core_root),
                "files": [str(f["name"]) for f in core.get_files(core_flags)],
            }

        self._cached_core_list_for_generator = out
        return out

    def run_generators(self):
        """ Run all generators """
        generated_libraries = {}
        for core in self.cores:
            logger.debug("Running generators in " + str(core.name))
            core_flags = self._core_flags(core)
            if hasattr(core, "get_ttptttg"):
                for ttptttg_data in core.get_ttptttg(core_flags):
                    ttptttg = Ttptttg(
                        ttptttg_data,
                        core,
                        self.generators,
                        core_list=self._core_list_for_generator(),
                    )
                    gen_lib = ttptttg.generate(self.work_root)

                    # The output directory of the generator can contain core
                    # files, which need to be added to the dependency tree.
                    # This isn't done instantly, but only after all generators
                    # have finished, to re-do the dependency resolution only
                    # once, and not once per generator run.
                    generator_name = ttptttg_data["generator"]
                    generated_libraries.setdefault(generator_name, []).append(gen_lib)

                    # Create a dependency to all generated cores.
                    # XXX: We need a cleaner API to the CoreManager to add
                    # these dependencies. Until then, explicitly use a private
                    # API to be reminded that this is a workaround.
                    gen_cores = self.core_manager.find_cores(gen_lib)
                    gen_core_vlnvs = [core.name for core in gen_cores]
                    logger.debug(
                        "The generator produced the following cores, which are inserted into the dependency tree: %s",
                        gen_cores,
                    )
                    core._generator_created_dependencies += gen_core_vlnvs

        # Make all new libraries known to fusesoc. This invalidates the solver
        # cache and is therefore quite expensive.
        for gen_name, libs in generated_libraries.items():
            for lib in libs:
                self.core_manager.add_library(lib, from_generator=gen_name)
        self._invalidate_cached_core_list_for_generator()

    def create_eda_api_struct(self):
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
                    shutil.copy2(os.path.join(files_root, file["name"]), dst)
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
            if snippet["vpi"]:
                self._cores_with_vpi.add(str(core.name))

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
        self.edalize = {
            "version": "0.2.1",
            "dependencies": {},
            "files": [],
            "hooks": {},
            "name": self.system_name or top_core.sanitized_name,
            "parameters": {},
            "tool_options": {},
            "toplevel": top_core.get_toplevel(self.flags),
            "vpi": [],
        }

        for snippet in first_snippets + snippets + last_snippets:
            merge_dict(self.edalize, snippet)

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
        tool_options = self.edalize["tool_options"][tool]

        for key, value in sorted(parsed_args.items()):
            if value is None:
                pass
            elif key in backend_members:
                tool_options[key] = value
            elif key in backend_lists:
                if not key in tool_options:
                    tool_options[key] = []
                tool_options[key] += value.split(" ")
            elif key in self.edalize["parameters"]:
                _param = self.edalize["parameters"][key]
                _param["default"] = value
            else:
                raise RuntimeError("Unknown parameter " + key)

    def _depgraph_to_mk(self, core_graph):
        """Convert a dependency graph into a Makefile fragment

        The dependency graph is expected to be in the form produced by
        CoreManager.get_dependency_graph().

        The Makefile fragment will define a variable called "fusesoc-deps"
        which contains a list of files. A downstream Makefile can have its
        'build' target depend on this list of files to rebuild when necessary.

        Note this is a little different from GCC-style .d files, which define a
        Make target that adds dependencies to the compiled object file. We
        can't do that here, because we don't know what the file is.

        All paths are absolute because the Makefile using this may run in a
        different directory from where fusesoc was run.

        Returns either the string contents of the Makefile to write or None (if
        there's some reason we shouldn't produce a Makefile for this core). In
        the latter case, it prints an info message.

        """
        cores = depgraph_cores(core_graph)
        dep_paths = []
        generator_names = set()

        for core in cores:
            # Makefile dependencies for cores with VPI information are not
            # currently supported (TODO?). Rather than spit out an incomplete
            # Makefile, which might cause a user to miss a rebuild, we don't
            # spit one out at all.
            if str(core.name) in self._cores_with_vpi:
                logger.info(
                    "Not writing Makefile because core {} has "
                    "VPI information (not currently supported).".format(str(core.name))
                )
                return None

            # Every core depends on its actual core file (since a change to
            # this might add other files to the file list)
            dep_paths.append(core.core_file)

            # It also depends on each file in its file list
            core_flags = self._core_flags(core)
            for core_file in core.get_files(core_flags):
                dep_paths.append(os.path.join(core.files_root, core_file["name"]))

            # Was this core generated?
            if core.from_generator is not None:
                generator_names.add(core.from_generator)

        # Some of the cores might have been auto-generated. In which case, we
        # also need to depend on their generators and the cores that contained
        # them.
        for gen_name in generator_names:
            # We know that gen_name is a valid key of self.generators (since it
            # got passed in when making a generated core in run_generators)
            gen_core_name, generator = self.generators[gen_name]

            # Add the .core file that defines the generator and the script that
            # it ran. Rather than iterating through self.cores, we cheat and
            # look up the name in self._core_list_for_generator(). While the
            # resulting dict doesn't have the core object, it does have an
            # entry for "core_filepath", which is what we need.
            core_dict = self._core_list_for_generator()[str(gen_core_name)]

            dep_paths.append(core_dict["core_filepath"])
            dep_paths.append(Ttptttg.generator_script(generator))

        # We now have a list of paths (relative to the current directory).
        return (
            "fusesoc-deps := \\\n  "
            + " \\\n  ".join(os.path.abspath(path) for path in dep_paths)
            + "\n"
        )

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

    def to_yaml(self, edalize_file):
        return utils.yaml_fwrite(edalize_file, self.edalize)


from fusesoc.core import Core
from fusesoc.utils import Launcher


class Ttptttg:
    def __init__(self, ttptttg, core, generators, core_list):
        generator_name = ttptttg["generator"]
        if generator_name not in generators:
            raise RuntimeError(
                "Could not find generator '{}' requested by {}".format(
                    generator_name, core.name
                )
            )
        self.generator = generators[generator_name][1]
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
            "cores": core_list,
        }

    def generate(self, outdir):
        """Run a parametrized generator

        Args:
            outdir (str): The directory where to store the generated cores

        Returns:
            Libary: A Library with the generated files
        """
        generator_cwd = os.path.join(outdir, "generated", self.vlnv.sanitized_name)
        generator_input_file = os.path.join(generator_cwd, self.name + "_input.yml")

        logger.info("Generating " + str(self.vlnv))
        if not os.path.exists(generator_cwd):
            os.makedirs(generator_cwd)
        utils.yaml_fwrite(generator_input_file, self.generator_input)

        args = [
            Ttptttg.generator_script(self.generator),
            os.path.abspath(generator_input_file),
        ]

        if self.generator.interpreter:
            args[0:0] = [self.generator.interpreter]

        Launcher(args[0], args[1:], cwd=generator_cwd).run()

        library_name = "generated-" + self.vlnv.sanitized_name
        return Library(name=library_name, location=generator_cwd)

    @staticmethod
    def generator_script(generator):
        """"Get the absolute path to the script for a generator"""
        return os.path.join(os.path.abspath(generator.root), generator.command)
