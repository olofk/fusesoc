import argparse
import logging
import os
import shutil
import yaml

from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)


class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        path = os.path.expandvars(values[0])
        path = os.path.expanduser(path)
        path = os.path.abspath(path)
        setattr(namespace, self.dest, [path])


class Edalizer(object):
    def __init__(
        self,
        vlnv,
        flags,
        cores,
        cache_root,
        work_root,
        export_root=None,
        system_name=None,
    ):
        if os.path.exists(work_root):
            for f in os.listdir(work_root):
                if os.path.isdir(os.path.join(work_root, f)):
                    shutil.rmtree(os.path.join(work_root, f))
                else:
                    os.remove(os.path.join(work_root, f))
        else:
            os.makedirs(work_root)

        logger.debug("Building EDA API")

        def merge_dict(d1, d2):
            for key, value in d2.items():
                if isinstance(value, dict):
                    d1[key] = merge_dict(d1.get(key, {}), value)
                elif isinstance(value, list):
                    d1[key] = d1.get(key, []) + value
                else:
                    d1[key] = value
            return d1

        generators = {}

        first_snippets = []
        snippets = []
        last_snippets = []
        _flags = flags.copy()
        core_queue = cores[:]
        core_queue.reverse()
        while core_queue:
            snippet = {}
            core = core_queue.pop()
            logger.info("Preparing " + str(core.name))
            core.setup()

            logger.debug("Collecting EDA API parameters from {}".format(str(core.name)))
            _flags["is_toplevel"] = core.name == vlnv

            # Extract direct dependencies
            snippet["dependencies"] = {str(core.name): getattr(core, "direct_deps", [])}

            # Extract files
            if export_root:
                files_root = os.path.join(export_root, core.sanitized_name)
                core.export(files_root, _flags)
            else:
                files_root = core.files_root

            rel_root = os.path.relpath(files_root, work_root)

            # Extract parameters
            snippet["parameters"] = core.get_parameters(_flags)

            # Extract tool options
            snippet["tool_options"] = {flags["tool"]: core.get_tool_options(_flags)}

            # Extract scripts
            snippet["hooks"] = core.get_scripts(rel_root, _flags)

            _files = []
            for file in core.get_files(_flags):
                if file.copyto:
                    _name = file.copyto
                    dst = os.path.join(work_root, _name)
                    _dstdir = os.path.dirname(dst)
                    if not os.path.exists(_dstdir):
                        os.makedirs(_dstdir)
                    shutil.copy2(os.path.join(files_root, file.name), dst)
                else:
                    _name = os.path.join(rel_root, file.name)
                _files.append(
                    {
                        "name": str(_name),
                        "core": str(core.name),
                        "file_type": file.file_type,
                        "is_include_file": file.is_include_file,
                        "logical_name": file.logical_name,
                    }
                )

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

            # Extract generators if defined in CAPI
            if hasattr(core, "get_generators"):
                generators.update(core.get_generators(_flags))

            # Run generators
            if hasattr(core, "get_ttptttg"):
                for ttptttg_data in core.get_ttptttg(_flags):
                    _ttptttg = Ttptttg(ttptttg_data, core, generators)
                    for gen_core in _ttptttg.generate(cache_root):
                        gen_core.pos = _ttptttg.pos
                        core_queue.append(gen_core)

            if hasattr(core, "pos"):
                if core.pos == "first":
                    first_snippets.append(snippet)
                elif core.pos == "last":
                    last_snippets.append(snippet)
                else:
                    snippets.append(snippet)
            else:
                snippets.append(snippet)

        top_core = cores[-1]
        self.edalize = {
            "version": "0.2.1",
            "dependencies": {},
            "files": [],
            "hooks": {},
            "name": system_name or top_core.sanitized_name,
            "parameters": {},
            "tool_options": {},
            "toplevel": top_core.get_toplevel(flags),
            "vpi": [],
        }

        for snippet in first_snippets + snippets + last_snippets:
            merge_dict(self.edalize, snippet)

    def _build_parser(self, backend_class):
        typedict = {
            "bool": {"action": "store_true"},
            "file": {"type": str, "nargs": 1, "action": FileAction},
            "int": {"type": int, "nargs": 1},
            "str": {"type": str, "nargs": 1},
        }
        progname = "fusesoc run {}".format(self.edalize["name"])

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
        for name, param in self.edalize["parameters"].items():
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
                        **typedict[param["datatype"]]
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

    def _add_parsed_args(self, backend_class, parsed_args):
        _opts = backend_class.get_doc(0)
        # Parse arguments
        backend_members = [x["name"] for x in _opts.get("members", [])]
        backend_lists = [x["name"] for x in _opts.get("lists", [])]
        known = parsed_args

        tool = backend_class.__name__.lower()
        tool_options = self.edalize["tool_options"][tool]

        for key, value in sorted(vars(known).items()):
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
                _value = value if type(value) == bool else value[0]
                _param["default"] = _value
            else:
                raise RuntimeError("Unknown parameter " + key)

    def parse_args(self, backend_class, backendargs):
        parser = self._build_parser(backend_class)
        parsed_args = parser.parse_args(backendargs)
        self._add_parsed_args(backend_class, parsed_args)

    def to_yaml(self, edalize_file):
        with open(edalize_file, "w") as f:
            f.write(yaml.dump(self.edalize))


from fusesoc.core import Core
from fusesoc.utils import Launcher


class Ttptttg(object):
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

    def generate(self, cache_root):
        """Run a parametrized generator

        Args:
            cache_root (str): The directory where to store the generated cores

        Returns:
            list: Cores created by the generator
        """
        generator_cwd = os.path.join(cache_root, "generated", self.vlnv.sanitized_name)
        generator_input_file = os.path.join(generator_cwd, self.name + "_input.yml")

        logger.info("Generating " + str(self.vlnv))
        if not os.path.exists(generator_cwd):
            os.makedirs(generator_cwd)
        with open(generator_input_file, "w") as f:
            f.write(yaml.dump(self.generator_input))

        args = [
            os.path.join(os.path.abspath(self.generator.root), self.generator.command),
            generator_input_file,
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
