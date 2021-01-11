# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

# XXX #1 (also referenced in the code below):
#       CAPI1 does not treat vhdl section as a fileset like it does with
#       verilog. See function _collect_filesets(self) of class Core in
#       fusesoc/capi1/core.py.
# XXX #2 (also referenced in the code below):
#       rivierapro is considered to be unsupported, according to the message in
#       the SimulatorList class in file fusesoc/capi1/section.py.
# XXX #3:
#       Verilator treated as a simulator in class SimulatorList in file
#       fusesoc/capi1/section.py, but meanwhile it is treated as a synthesizer
#       in function _get_flow in file fusesoc/capi1/core.py.
#       This converter definitely treat Verilator as a synthesizer.
# XXX #4:
#       Yaml dumper does not indent file lists, may be a little uncomfortable
# XXX #5:
#       Scripts migration is not so simple: if CAPI1 is used, then the
#       ../sw/<corename>/ prefix added before script and written to the
#       <corename>.eda.yml file, but CAPI2 core have to have explicit full file
#       path. Probably script file must be added to a new fileset and have a
#       'copyto' flag set or just set env if it is possible.
# NOTE: Untested tools on converted cores:
#           Vivado
#           Icestorm
#           Trellis
#           ISE
#           modelsim
#           isim
#           xsim
# NOTE: Verilator is tested: for or1200-generic from orpsoc-cores fusesoc
#       produces functionally identical files in the build directory
#       (especially .vc file) with the following command:
#         fusesoc --verbose run --tool=verilator --target=synth or1200-generic
#       <corename>.eda.yml file, which is produced from the converted CAPI2
#       core, does not contain 'top_module' entry, everything else stays the
#       same.
# NOTE: Quartus and parameters are tested: for de0_nano from fusesoc-core
#       fusesoc produces almost everything the same except for a scripts env.

import logging
import os
import sys

import yaml

from fusesoc.capi1.core import Core as Capi1Core
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)

SCRIPT_TYPES = ["pre_build_scripts", "pre_run_scripts", "post_run_scripts"]


def gather_vpi(core):
    vpi = {}

    for vpi_fileset in ["include_files", "src_files"]:
        if hasattr(core.vpi, vpi_fileset) and getattr(core.vpi, vpi_fileset):
            if "filesets" not in vpi:
                vpi["filesets"] = []
            vpi["filesets"].append("vpi_" + vpi_fileset)

    if core.vpi.libs:
        vpi["libs"] = core.vpi.libs

    return {"vpi": vpi}


def gather_parameters(core):
    parameters = {}
    for key, value in core.parameter.items():
        parameters[key] = {}
        attributes = ["datatype", "default", "description", "paramtype", "scope"]
        for attr in filter(lambda a: getattr(value, a), attributes):
            parameters[key][attr] = getattr(value, attr)

    return parameters


def gather_scripts(core):
    scripts = {}
    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                scripts[script] = {
                    "cmd": [
                        "sh",
                        os.path.join(
                            "..",
                            "src",
                            core.name.sanitized_name,
                            getattr(core.scripts, script)[0],
                        ),
                    ]
                }
    return scripts


def gather_default(core):
    default = {"filesets": []}

    for fileset in core.file_sets:
        if fileset.private == False and fileset.file:
            default["filesets"].append(fileset.name)

    # XXX #1 (see the top of the file):
    # CAPI1 does not treat vhdl section as fileset like it does with verilog
    if core.vhdl and core.vhdl.src_files:
        # this check made for forward compatibility
        if "vhdl_src_files" not in default["filesets"]:
            default["filesets"].append("vhdl_src_files")

    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                default["filesets"].append(script)

    hooks = gather_hooks(core)
    if hooks:
        default["hooks"] = hooks

    parameters = gather_target_parameters(core)
    if parameters:
        default["parameters"] = parameters

    if core.vpi:
        default["vpi"] = ["vpi"]

    return default


def gather_target_parameters(core):
    parameters = []
    for parameter in core.parameter:
        parameters.append(parameter)

    return parameters


def gather_hooks(core):
    hooks = {}
    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                hooks[script[:-8]] = [script]

    return hooks


def strip_quotes(s):
    if isinstance(s, str):
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]

    return s


def gather_tool(core, toolname, attributes):
    tool = {}
    for attr in attributes:
        if hasattr(getattr(core, toolname), attr):
            if getattr(getattr(core, toolname), attr):
                # Avoid quotes on a part name
                tool[attr] = strip_quotes(getattr(getattr(core, toolname), attr))

    if toolname == "verilator":
        if core.verilator.source_type == "systemC":
            tool["mode"] = "sc"
        else:
            tool["mode"] = "cc"

        if core.verilator.cli_parser == "fusesoc":
            tool["cli_parser"] = "managed"
        elif core.verilator.cli_parser == "":
            tool["cli_parser"] = "passthrough"

    return tool


def gather_sim_tools(core):
    sim_tools = {
        "ghdl": ["analyze_options", "run_options"],
        "icarus": ["iverilog_options"],
        "modelsim": ["vlog_options", "vsim_options"],
        "isim": ["isim_options"],
        # XXX #2 (see the top of the file);
        # rivierapro is considered to be unsupported
        "rivierapro": ["vlog_options", "vsim_options"],
        "xsim": ["xsim_options"],
    }
    tools = {}
    for simulator in core.simulators:
        tool = gather_tool(core, simulator, sim_tools[simulator])
        if tool:
            tools[simulator] = tool

    return tools


def gather_sim_filesets(core):
    filesets = []
    for fileset in core.file_sets:
        if "sim" in fileset.usage:
            filesets.append(fileset.name)

    # XXX #1 (see the top of the file):
    # CAPI1 does not treat vhdl section as fileset like it does with verilog
    if core.vhdl and core.vhdl.src_files:
        if "vhdl_src_files" not in filesets:
            filesets.append("vhdl_src_files")

    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                filesets.append(script)

    return filesets


def gather_sim(core):
    sim = {}

    filesets = gather_sim_filesets(core)
    if filesets:
        sim["filesets"] = filesets

    tools = gather_sim_tools(core)
    if tools:
        sim["tools"] = tools

    if len(core.simulators):
        sim["default_tool"] = core.simulators[0]

    hooks = gather_hooks(core)
    if hooks:
        sim["hooks"] = hooks

    parameters = gather_target_parameters(core)
    if parameters:
        sim["parameters"] = parameters

    if core.vpi:
        sim["vpi"] = ["vpi"]

    return sim


def gather_synth_filesets(core, synth_tools):
    filesets = []
    for fileset in core.file_sets:
        if set(["synth"] + synth_tools) & set(fileset.usage) and fileset.file:
            filesets.append(fileset.name)

    # XXX #1 (see the top of the file):
    # CAPI1 does not treat vhdl section as fileset like it does with verilog
    if core.vhdl and core.vhdl.src_files:
        # this check made for forward compatibility
        if "vhdl_src_files" not in filesets:
            filesets.append("vhdl_src_files")

    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                filesets.append(script)

    return filesets


def gather_synth(core):
    synth_tools = {
        "icestorm": [
            "pcf_file",
            "arachne_pnr_options",
            "yosys_synth_options",
        ],
        "ise": ["family", "device", "package"],
        "quartus": [
            "qsys_files",
            "sdc_files",
            "tcl_files",
            "quartus_options",
            "family",
            "device",
        ],
        "verilator": ["cli_parser", "verilator_options", "libs"],
        "vivado": ["part"],
        "trellis": [
            "nextpnr_options",
            "yosys_synth_options",
        ],
    }
    synth = {}

    filesets = gather_synth_filesets(core, list(synth_tools))
    if filesets:
        synth["filesets"] = filesets

    for tool in synth_tools.keys():
        if getattr(core, tool):
            synth["tools"] = {tool: {}}
            synth["tools"][tool] = gather_tool(core, tool, synth_tools[tool])
            synth["toplevel"] = getattr(core, tool).top_module
            synth["default_tool"] = tool

    hooks = gather_hooks(core)
    if hooks:
        synth["hooks"] = hooks

    parameters = gather_target_parameters(core)
    if parameters:
        synth["parameters"] = parameters

    if core.vpi:
        synth["vpi"] = ["vpi"]

    return synth


def gather_targets(core):
    targets = {}

    default = gather_default(core)
    if default:
        targets["default"] = default

    sim = gather_sim(core)
    if sim:
        targets["sim"] = sim

    synth = gather_synth(core)
    if synth:
        targets["synth"] = synth

    # Undocumented [simulator] section with 'toplevel' member
    for simulator in core.simulator:
        if "sim" not in targets:
            targets["sim"] = {}
        targets["sim"][simulator] = core.simulator[simulator]

    return targets


def gather_sim_depend(core):
    sim_depend = []
    for simulator in core.simulators:
        if hasattr(getattr(core, simulator), "depend"):
            for depend in getattr(core, simulator).depend:
                depend_fullname = depend.depstr()
                if depend_fullname not in sim_depend:
                    sim_depend.append(depend_fullname)

    return sim_depend


def gather_common_depend(core):
    common_depend = []
    for depend in core.main.depend:
        depend_fullname = depend.depstr()
        if depend_fullname not in common_depend:
            common_depend.append(depend_fullname)
    return common_depend


def gather_fileset_depend(core, fileset):
    if len(fileset.usage) == 1 and "sim" in fileset.usage:
        sim_depend = gather_sim_depend(core)
        if len(sim_depend):
            return sim_depend

    if "sim" in fileset.usage and "synth" in fileset.usage:
        common_depend = gather_common_depend(core)
        if len(common_depend):
            return common_depend

    return []


def get_common_filetype(fileset):
    types = {}
    for file in fileset.file:
        if file.file_type in types:
            types[file.file_type] += 1
        else:
            types[file.file_type] = 1

    if types:
        return max(types, key=types.get)


def gather_files(fileset):
    common_type = get_common_filetype(fileset)
    files = []
    for file in fileset.file:
        filename = file.name

        if file.is_include_file == True:
            filename = {}
            filename[file.name] = {"is_include_file": True}

        if file.file_type != common_type:
            if type(filename) == str:
                filename = {}
            filename[file.name] = {"file_type": file.file_type}
        files.append(filename)

    return files


def gather_filesets(core):
    filesets = {}
    for fileset in core.file_sets:
        files = gather_files(fileset)
        if files:
            filesets[fileset.name] = {}
            filesets[fileset.name]["files"] = files
        else:
            continue

        file_type = get_common_filetype(fileset)
        if file_type:
            filesets[fileset.name]["file_type"] = file_type

        fileset_depend = gather_fileset_depend(core, fileset)
        if fileset_depend:
            filesets[fileset.name]["depend"] = fileset_depend

    # XXX #1 (see the top of the file):
    # CAPI1 does not treat vhdl section as fileset like it does with verilog
    if core.vhdl and core.vhdl.src_files:
        # this check made for forward compatibility
        if "vhdl_src_files" not in filesets:
            filesets["vhdl_src_files"] = {}
            filesets["vhdl_src_files"]["files"] = core.vhdl.src_files
            filesets["vhdl_src_files"]["file_type"] = "vhdlSource"

    if hasattr(core.vpi, "src_files") and getattr(core.vpi, "src_files"):
        filesets["vpi_src_files"] = {"files": []}
        for file in getattr(core.vpi, "src_files"):
            filesets["vpi_src_files"]["files"].append(file.name)

    if hasattr(core.vpi, "include_files") and getattr(core.vpi, "include_files"):
        filesets["vpi_include_files"] = {"files": []}
        for file in getattr(core.vpi, "include_files"):
            filesets["vpi_include_files"]["files"].append(
                {file.name: {"is_include_file": "true"}}
            )

    for script in SCRIPT_TYPES:
        if hasattr(core.scripts, script):
            if getattr(core.scripts, script):
                if script not in filesets:
                    filesets[script] = {"files": []}
                    filesets[script] = {"file_type": "user"}
                filesets[script]["files"] = getattr(core.scripts, script)

    return filesets


def write_core(core_file, coredata):
    with open(core_file, "w") as f:
        f.write("CAPI=2:\n")

        noalias_dumper = yaml.dumper.SafeDumper
        noalias_dumper.ignore_aliases = lambda self, data: True
        yaml.dump(coredata, f, default_flow_style=False, Dumper=noalias_dumper)


def open_core(capi1_file):
    with open(capi1_file) as f:
        first_line = f.readline().split()[0]
        if first_line == "CAPI=1":
            return Capi1Core(capi1_file)
        elif first_line == "SAPI=1":
            logger.error("You must specify a core file, not a system file")
        elif first_line == "CAPI=2:":
            logger.error("Input file must be in CAPI1 format")
        else:
            logger.error("Unknown file type")
    return 0


def convert_core(capi1_file, capi2_file):
    try:
        core = open_core(capi1_file)
        if not core:
            return

        coredata = {}
        coredata["name"] = str(core.name)

        if core.main.description:
            coredata["description"] = strip_quotes(core.main.description)

        if core.provider:
            coredata["provider"] = core.provider.config

        if core.scripts:
            coredata["scripts"] = gather_scripts(core)

        filesets = gather_filesets(core)
        if filesets:
            coredata["filesets"] = filesets

        targets = gather_targets(core)
        if targets:
            coredata["targets"] = targets

        if core.parameter:
            parameters = gather_parameters(core)
            if parameters:
                coredata["parameters"] = parameters

        if core.vpi:
            coredata["vpi"] = gather_vpi(core)

        write_core(capi2_file, coredata)
    except Exception as e:
        logger.error("Unable to convert core {}: {}".format(capi1_file, str(e)))
        sys.exit(1)
