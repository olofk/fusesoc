#!/usr/bin/env python
# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import os
import shutil
import signal
import subprocess
import sys
import warnings
from importlib import import_module

from fusesoc import __version__

# Check if this is run from a local installation
fusesocdir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
)
if os.path.exists(os.path.join(fusesocdir, "fusesoc")):
    sys.path[0:0] = [fusesocdir]

import logging

try:
    from edalize.edatool import get_edatool
except ImportError:
    from edalize import get_edatool

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager, DependencyError
from fusesoc.edalizer import Edalizer
from fusesoc.librarymanager import Library
from fusesoc.utils import Launcher, setup_logging, yaml_fread
from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)


def _get_core(cm, name):
    core = None
    try:
        core = cm.get_core(Vlnv(name))
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except DependencyError as e:
        logger.error(
            f"{name!r} or any of its dependencies requires {e.value!r}, but "
            "this core was not found"
        )
        exit(1)
    return core


def abort_handler(signal, frame):
    print("")
    logger.info("****************************")
    logger.info("****   FuseSoC aborted  ****")
    logger.info("****************************")
    print("")
    sys.exit(0)


signal.signal(signal.SIGINT, abort_handler)


def pgm(cm, args):
    warnings.warn(
        "The 'pgm' subcommand has been removed. "
        "Use 'fusesoc run --target=synth --run' instead."
    )


def fetch(cm, args):
    core = _get_core(cm, args.core)

    try:
        core.setup()
    except RuntimeError as e:
        logger.error("Failed to fetch '{}': {}".format(core.name, str(e)))
        exit(1)


def list_paths(cm, args):
    cores_root = [x.location for x in cm.get_libraries()]
    print("\n".join(cores_root))


def add_library(cm, args):
    sync_uri = vars(args)["sync-uri"]

    if args.location:
        location = args.location
    elif vars(args).get("global", False):
        location = os.path.join(cm._lm.library_root, args.name)
    else:
        location = os.path.join("fusesoc_libraries", args.name)

    sync_type = vars(args).get("sync-type")
    sync_version = vars(args).get("sync-version")

    # Check if it's a dir. Otherwise fall back to git repo
    if not sync_type:
        if os.path.isdir(sync_uri):
            sync_type = "local"
        else:
            sync_type = "git"

    if sync_type == "local":
        logger.info(
            "Interpreting sync-uri '{}' as location for local provider.".format(
                sync_uri
            )
        )
        location = os.path.abspath(sync_uri)

    auto_sync = not args.no_auto_sync
    library = Library(args.name, location, sync_type, sync_uri, sync_version, auto_sync)

    if args.config:
        config = Config(args.config)
    elif vars(args)["global"]:
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )
        config_file = os.path.join(xdg_config_home, "fusesoc", "fusesoc.conf")
        config = Config(config_file)
    else:
        config = Config("fusesoc.conf")

    try:
        config.add_library(library)
    except RuntimeError as e:
        logger.error("`add library` failed: " + str(e))
        exit(1)


def library_list(cm, args):
    lengths = [4, 8, 9, 8, 12, 9]
    for lib in cm.get_libraries():
        lengths[0] = max(lengths[0], len(lib.name))
        lengths[1] = max(lengths[1], len(lib.location))
        lengths[2] = max(lengths[2], len(lib.sync_type))
        lengths[3] = max(lengths[3], len(lib.sync_uri or ""))
        lengths[4] = max(lengths[4], len(lib.sync_version or ""))
    print(
        "{} : {} : {} : {} : {} : {}".format(
            "Name".ljust(lengths[0]),
            "Location".ljust(lengths[1]),
            "Sync type".ljust(lengths[2]),
            "Sync URI".ljust(lengths[3]),
            "Sync version".ljust(lengths[4]),
            "Auto sync".ljust(lengths[5]),
        )
    )
    for lib in cm.get_libraries():
        print(
            "{} : {} : {} : {} : {} : {}".format(
                lib.name.ljust(lengths[0]),
                lib.location.ljust(lengths[1]),
                lib.sync_type.ljust(lengths[2]),
                (lib.sync_uri or "N/A").ljust(lengths[3]),
                (lib.sync_version or "(none)").ljust(lengths[4]),
                ("y" if lib.auto_sync else "n").ljust(lengths[5]),
            )
        )


def list_cores(cm, args):
    cores = cm.get_cores()
    print("\nAvailable cores:\n")
    if not cores:
        cores_root = cm.get_libraries()
        if cores_root:
            logger.error("No cores found in any library")
        else:
            logger.error("No libraries registered")
        exit(1)
    maxlen = max(map(len, cores.keys()))
    print("Core".ljust(maxlen) + "  Cache status  Description")
    print("=" * 80)
    for name in sorted(cores.keys()):
        core = cores[name]
        print(
            name.ljust(maxlen)
            + " : "
            + core.cache_status().rjust(10)
            + " : "
            + (core.get_description() or "<No description>")
        )


def list_tools(cm, args):
    from edalize.edatool import walk_tool_packages

    _tp = list(walk_tool_packages())
    maxlen = max(map(len, _tp))

    for tool_name in _tp:
        try:
            tool_class = get_edatool(tool_name)
            desc = tool_class.get_doc(0)["description"]
            print(f"{tool_name:{maxlen}} : {desc}")
        # Ignore any misbehaving backends
        except Exception:
            pass


def gen_list(cm, args):
    cores = cm.get_generators()
    if not cores:
        print("\nNo available generators\n")
    else:
        print("\nAvailable generators:\n")
        maxlen = max(map(len, cores.keys()))
        print("Core".ljust(maxlen) + "   Generator")
        print("=" * (maxlen + 12))
        for core in sorted(cores.keys()):
            for generator_name, generator_data in cores[core].items():
                print(
                    "{} : {} : {}".format(
                        core.ljust(maxlen),
                        generator_name,
                        generator_data["description"] or "<No description>",
                    )
                )


def gen_show(cm, args):
    cores = cm.get_generators()
    for core in sorted(cores.keys()):
        for generator_name, generator_data in cores[core].items():
            if generator_name == args.generator:
                print(
                    """
Core        : {}
Generator   : {}
Description : {}
Usage       :

{}""".format(
                        core,
                        generator_name,
                        generator_data["description"] or "<No description>",
                        generator_data["usage"] or "",
                    )
                )


def core_info(cm, args):
    core = _get_core(cm, args.core)
    print(core.info())


def gen_clean(cm, args):
    cachedir = os.path.join(cm.config.cache_root, "generator_cache")
    shutil.rmtree(cachedir, ignore_errors=True)
    print(f"Cleaned generator cache: {cachedir}")


def run(cm, args):
    stages = (args.setup, args.build, args.run)

    # Always run setup if build is true
    args.setup |= args.build

    # Run all stages by default if no stage flags are set
    if stages == (False, False, False):
        do_configure = True
        do_build = True
        do_run = True
    elif stages == (True, False, True):
        logger.error("Configure and run without build is invalid")
        exit(1)
    else:
        do_configure = args.setup
        do_build = args.build
        do_run = args.run

    flags = {"target": args.target or "default"}
    if args.tool:
        flags["tool"] = args.tool
    for flag in args.flag:
        if flag[0] == "+":
            flags[flag[1:]] = True
        elif flag[0] == "-":
            flags[flag[1:]] = False
        else:
            flags[flag] = True

    run_backend(
        cm,
        not args.no_export,
        do_configure,
        do_build,
        do_run,
        flags,
        args.system_name,
        args.system,
        args.backendargs,
        args.build_root,
        args.verbose,
        args.resolve_env_vars_early,
    )


# Clean out old work root
def prepare_work_root(work_root):
    if os.path.exists(work_root):
        for f in os.listdir(work_root):
            if os.path.isdir(os.path.join(work_root, f)):
                shutil.rmtree(os.path.join(work_root, f))
            else:
                os.remove(os.path.join(work_root, f))
    else:
        os.makedirs(work_root)


def run_backend(
    cm,
    export,
    do_configure,
    do_build,
    do_run,
    flags,
    system_name,
    system,
    backendargs,
    build_root_arg,
    verbose,
    resolve_env_vars=False,
):
    tool_error = (
        "No flow or tool was supplied on command line or found in '{}' core description"
    )
    core = _get_core(cm, system)

    target = flags["target"]

    flow = core.get_flow(flags)
    try:
        flags = dict(core.get_flags(target), **flags)
    except SyntaxError as e:
        logger.error(str(e))
        exit(1)

    if flow:
        logger.debug(f"Using flow API (flow={flow})")
    else:
        logger.debug("flow not set. Falling back to tool API")
        if "tool" in flags:
            tool = flags["tool"]
        else:
            logger.error(tool_error.format(system))
            exit(1)

    build_root = build_root_arg or os.path.join(
        cm.config.build_root, core.name.sanitized_name
    )
    logger.debug(f"Setting build_root to {build_root}")

    if flow:
        work_root = os.path.join(build_root, target)
    else:
        work_root = os.path.join(build_root, f"{target}-{tool}")

    edam_file = os.path.join(work_root, core.name.sanitized_name + ".eda.yml")

    logger.debug(f"Setting work_root to {work_root}")

    if export and not "no_export" in flags.keys():
        export_root = os.path.join(work_root, "src")
        logger.debug(f"Setting export_root to {export_root}")
    else:
        export_root = None

    backend_class = None
    if flow:
        try:
            backend_class = getattr(
                import_module(f"edalize.flows.{flow}"), flow.capitalize()
            )
        except ModuleNotFoundError:
            logger.error(f"Flow {flow!r} not found")
            exit(1)
        except ImportError:
            logger.error("Selected Edalize version does not support the flow API")
            exit(1)

    else:
        try:
            backend_class = get_edatool(tool)
        except ImportError:
            logger.error(f"Backend {tool!r} not found")
            exit(1)

    edalizer = Edalizer(
        toplevel=core.name,
        flags=flags,
        core_manager=cm,
        work_root=work_root,
        export_root=export_root,
        system_name=system_name,
        resolve_env_vars=resolve_env_vars,
    )

    # Unconditionally clean out the work root on fresh builds
    # if we use the old tool API
    if do_configure and not flow:
        prepare_work_root(work_root)

    try:
        edam = edalizer.run()
        edalizer.parse_args(backend_class, backendargs, edam)
        edalizer.export()
    except SyntaxError as e:
        logger.error(e.msg)
        exit(1)
    except RuntimeError as e:
        logger.error("Setup failed : {}".format(str(e)))
        exit(1)

    if os.path.exists(edam_file):
        old_edam = yaml_fread(edam_file, resolve_env_vars)
    else:
        old_edam = None

    if edam != old_edam:
        edalizer.to_yaml(edam_file)

    # Frontend/backend separation

    try:
        backend = backend_class(edam=edam, work_root=work_root, verbose=verbose)

    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except FileNotFoundError as e:
        logger.error(f'Could not find EDA API file "{e.filename}"')
        exit(1)

    makefile = os.path.join(work_root, "Makefile")
    do_configure = not os.path.exists(makefile) or (
        os.path.getmtime(makefile) < os.path.getmtime(edam_file)
    )

    if do_configure:
        try:
            backend.configure()
        except RuntimeError as e:
            logger.error("Failed to configure the system")
            logger.error(str(e))
            exit(1)

    if do_build:
        try:
            backend.build()
        except RuntimeError as e:
            logger.error("Failed to build {} : {}".format(str(core.name), str(e)))
            exit(1)

    if do_run:
        try:
            backend.run()
        except RuntimeError as e:
            logger.error("Failed to run {} : {}".format(str(core.name), str(e)))
            exit(1)


def update(cm, args):
    cm._lm.update(args.libraries)


def init_logging(verbose, monochrome, log_file=None):
    level = logging.DEBUG if verbose else logging.INFO

    setup_logging(level, monochrome, log_file)

    if verbose:
        logger.debug("Verbose output")
    else:
        logger.debug("Concise output")

    if monochrome:
        logger.debug("Monochrome output")
    else:
        logger.debug("Colorful output")


def init_coremanager(
    config,
    args_cores_root,
    args_resolve_env_vars=False,
    args_allow_additional_properties=False,
):
    logger.debug("Initializing core manager")
    cm = CoreManager(
        config,
        resolve_env_vars=args_resolve_env_vars,
        allow_additional_properties=args_allow_additional_properties,
    )

    args_libs = [Library(acr, acr) for acr in args_cores_root]
    # Add libraries from config file, env var and command-line
    for library in config.libraries + args_libs:
        try:
            cm.add_library(library, config.ignored_dirs)
        except (RuntimeError, OSError) as e:
            _s = "Failed to register library '{}'"
            logger.warning(_s.format(str(e)))

    return cm


def get_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global actions
    parser.add_argument(
        "--version",
        help="Display the FuseSoC version",
        action="version",
        version=__version__,
    )

    # Global options
    parser.add_argument(
        "--cores-root",
        help="Add additional directories containing cores",
        default=[],
        action="append",
    )
    parser.add_argument("--config", help="Specify the config file to use")
    parser.add_argument(
        "--monochrome",
        help="Don't use color for messages",
        action="store_true",
        default=not sys.stdout.isatty(),
    )
    parser.add_argument("--verbose", help="More info messages", action="store_true")
    parser.add_argument("--log-file", help="Write log messages to file")

    # fetch subparser
    parser_fetch = subparsers.add_parser(
        "fetch", help="Fetch a remote core and its dependencies to local cache"
    )
    parser_fetch.add_argument("core")
    parser_fetch.set_defaults(func=fetch)

    # core subparser
    parser_core = subparsers.add_parser(
        "core", help="Subcommands for dealing with cores"
    )
    core_subparsers = parser_core.add_subparsers()
    parser_core.set_defaults(subparser=parser_core)

    # core list subparser
    parser_core_list = core_subparsers.add_parser("list", help="List available cores")
    parser_core_list.set_defaults(func=list_cores)

    # core show subparser
    parser_core_show = core_subparsers.add_parser(
        "show", help="Show information about a core"
    )
    parser_core_show.add_argument("core", help="Name of the core to show")
    parser_core_show.set_defaults(func=core_info)

    # tool subparser
    parser_tool = subparsers.add_parser(
        "tool", help="Subcommands for dealing with tools"
    )
    tool_subparsers = parser_tool.add_subparsers()
    parser_tool.set_defaults(subparser=parser_tool)

    # tool list subparser
    parser_tool_list = tool_subparsers.add_parser("list", help="List available tools")
    parser_tool_list.set_defaults(func=list_tools)

    # list-cores subparser
    parser_list_cores = subparsers.add_parser("list-cores", help="List available cores")
    parser_list_cores.set_defaults(func=list_cores)

    # core-info subparser
    parser_core_info = subparsers.add_parser(
        "core-info", help="Display details about a core"
    )
    parser_core_info.add_argument("core")
    parser_core_info.set_defaults(func=core_info)

    # gen subparser
    parser_gen = subparsers.add_parser(
        "gen", help="Run or show information about generators"
    )
    parser_gen.set_defaults(subparser=parser_gen)
    gen_subparsers = parser_gen.add_subparsers()

    # gen list subparser
    parser_gen_list = gen_subparsers.add_parser(
        "list", help="List available generators"
    )
    parser_gen_list.set_defaults(func=gen_list)

    # gen show subparser
    parser_gen_show = gen_subparsers.add_parser(
        "show", help="Show information about a generator"
    )
    parser_gen_show.add_argument("generator", help="Name of the generator to show")
    parser_gen_show.set_defaults(func=gen_show)

    # gen clean subparser
    parser_gen_clean = gen_subparsers.add_parser(
        "clean", help="Clean generator cache directory"
    )
    parser_gen_clean.set_defaults(func=gen_clean)

    # list-paths subparser
    parser_list_paths = subparsers.add_parser(
        "list-paths", help="Display the search order for core root paths"
    )
    parser_list_paths.set_defaults(func=list_paths)

    # library subparser
    parser_library = subparsers.add_parser(
        "library", help="Subcommands for dealing with library management"
    )
    library_subparsers = parser_library.add_subparsers()
    parser_library.set_defaults(subparser=parser_library)

    # library add subparser
    parser_library_add = library_subparsers.add_parser(
        "add", help="Add new library to fusesoc.conf"
    )
    parser_library_add.add_argument("name", help="A friendly name  for the library")
    parser_library_add.add_argument(
        "sync-uri", help="The URI source for the library (can be a file system path)"
    )
    parser_library_add.add_argument(
        "--sync-version",
        help="Optionally specify the version of the library to use, for providers that support it",
        dest="sync-version",
    )
    parser_library_add.add_argument(
        "--location",
        help="The location to store the library into (defaults to $XDG_DATA_HOME/[name])",
    )
    parser_library_add.add_argument(
        "--sync-type",
        help="The provider type for the library. Defaults to 'git'.",
        choices=["git", "local"],
        dest="sync-type",
    )
    parser_library_add.add_argument(
        "--no-auto-sync",
        action="store_true",
        help="Disable automatic updates of the library",
    )
    parser_library_add.add_argument(
        "--global",
        action="store_true",
        help="Use the global FuseSoC config file in $XDG_CONFIG_HOME/fusesoc/fusesoc.conf",
    )
    parser_library_add.set_defaults(func=add_library)

    # library list subparser
    parser_library_list = library_subparsers.add_parser(
        "list", help="List core libraries"
    )
    parser_library_list.set_defaults(func=library_list)

    # library update subparser
    parser_library_update = library_subparsers.add_parser(
        "update", help="Update the FuseSoC core libraries"
    )
    parser_library_update.add_argument(
        "libraries", nargs="*", help="The libraries to update (defaults to all)"
    )
    parser_library_update.set_defaults(func=update)

    # run subparser
    parser_run = subparsers.add_parser("run", help="Start a tool flow")
    parser_run.add_argument(
        "--no-export",
        action="store_true",
        help="Reference source files from their current location instead of exporting to a build tree",
    )
    parser_run.add_argument(
        "--build-root", help="Output directory for build. Defaults to build/$VLNV"
    )
    parser_run.add_argument("--setup", action="store_true", help="Execute setup stage")
    parser_run.add_argument("--build", action="store_true", help="Execute build stage")
    parser_run.add_argument("--run", action="store_true", help="Execute run stage")
    parser_run.add_argument("--target", help="Override default target")
    parser_run.add_argument("--tool", help="Override default tool for target")
    parser_run.add_argument(
        "--flag",
        help="Set custom use flags. Can be specified multiple times",
        action="append",
        default=[],
    )
    parser_run.add_argument(
        "--resolve-env-vars-early",
        action="store_true",
        help="Resolve environment variables in FuseSoC (defaults to no resolution)",
    )
    parser_run.add_argument(
        "--system-name", help="Override default VLNV name for system"
    )
    parser_run.add_argument(
        "--allow-additional-properties",
        action="store_true",
        help="Allow additional properties in core files",
    )
    parser_run.add_argument("system", help="Select a system to operate on")
    parser_run.add_argument(
        "backendargs", nargs=argparse.REMAINDER, help="arguments to be sent to backend"
    )
    parser_run.set_defaults(func=run)

    return parser


def parse_args(argv):
    parser = get_parser()

    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args
    if hasattr(args, "subparser"):
        args.subparser.print_help()
    else:
        parser.print_help()
        return None


def fusesoc(args):
    init_logging(args.verbose, args.monochrome, args.log_file)
    config = Config(args.config)

    resolve_env_vars_early = False
    if hasattr(args, "resolve_env_vars_early"):
        resolve_env_vars_early = args.resolve_env_vars_early

    allow_additional_properties = False
    if hasattr(args, "allow_additional_properties"):
        allow_additional_properties = args.allow_additional_properties

    cm = init_coremanager(
        config, args.cores_root, resolve_env_vars_early, allow_additional_properties
    )
    # Run the function
    args.func(cm, args)


def main():
    args = parse_args(sys.argv[1:])
    if not args:
        exit(0)

    logger.debug("Command line arguments: " + str(sys.argv))

    fusesoc(args)


if __name__ == "__main__":
    main()
