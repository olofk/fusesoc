#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

import argparse
import os
import pathlib
import shutil
import signal
import sys
import warnings
from pathlib import Path

import argcomplete

from fusesoc import signature

try:
    from fusesoc.version import version as __version__
except ImportError:
    __version__ = "unknown"

# Check if this is run from a local installation
fusesocdir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
)
if os.path.exists(os.path.join(fusesocdir, "fusesoc")):
    sys.path[0:0] = [fusesocdir]

import logging

from fusesoc.config import Config
from fusesoc.coremanager import DependencyError
from fusesoc.fusesoc import Fusesoc
from fusesoc.librarymanager import Library

logger = logging.getLogger(__name__)


def _get_core(cm, name):
    matches = set()
    if not ":" in name:
        for core in cm.get_cores():
            (v, l, n, _) = core.split(":")
            if n.lower() == name.lower():
                matches.add(f"{v}:{l}:{n}")
        if len(matches) == 1:
            name = matches.pop()
        elif len(matches) > 1:
            _s = f"'{name}' is ambiguous. Potential matches: "
            _s += ", ".join(f"'{x}'" for x in matches)
            logger.error(_s)
            exit(1)

    core = None
    try:
        core = cm.get_core(name)
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except DependencyError as e:
        logger.error(
            f"{name!r} or any of its dependencies requires {e.value!r}, but "
            "this core was not found"
        )
        exit(1)
    except SyntaxError as e:
        logger.error(str(e))
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


def pgm(fs, args):
    warnings.warn(
        "The 'pgm' subcommand has been removed. "
        "Use 'fusesoc run --target=synth --run' instead."
    )


def fetch(fs, args):
    core = _get_core(fs, args.core)

    try:
        core.setup()
    except RuntimeError as e:
        logger.error("Failed to fetch '{}': {}".format(core.name, str(e)))
        exit(1)


def list_paths(fs, args):
    cores_root = [x.location for x in fs.get_libraries()]
    print("\n".join(cores_root))


def add_library(fs, args):
    sync_uri = vars(args)["sync-uri"]

    name = args.name or os.path.basename(sync_uri.rstrip("/"))

    # Check where to store the library
    if args.location:
        location = args.location
    elif vars(args).get("global", False):
        location = os.path.join(fs.config.library_root, name)
    else:
        location = os.path.join("fusesoc_libraries", name)

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
    library = Library(name, location, sync_type, sync_uri, sync_version, auto_sync)

    if args.config:
        config = Config(args.config)
    elif vars(args)["global"]:
        xdg_config_home = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        config_file = os.path.join(xdg_config_home, "fusesoc", "fusesoc.conf")
        config = Config(config_file)
    else:
        config = Config("fusesoc.conf")

    try:
        config.add_library(library)
    except RuntimeError as e:
        logger.error("`add library` failed: " + str(e))
        exit(1)


def library_list(fs, args):
    lengths = [4, 8, 9, 8, 12, 9]
    for lib in fs.get_libraries():
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
    for lib in fs.get_libraries():
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


def list_cores(fs, args):
    cores = fs.get_cores()
    trustfile = fs.config.ssh_trustfile or args.ssh_trustfile
    if not trustfile:
        logger.warn(
            "No trustfile configured (ssh-trustfile in fusesoc.conf), signatures will not be checked."
        )
    elif not os.path.isfile(trustfile):
        logger.warn(
            "The trustfile configured in fusesoc.conf does not exist, signatures will not be checked."
        )
    print("\nAvailable cores:\n")
    if not cores:
        cores_root = fs.get_libraries()
        if cores_root:
            logger.error("No cores found in any library")
        else:
            logger.error("No libraries registered")
        exit(1)
    maxlen = max(map(len, cores.keys()))
    print("Core".ljust(maxlen) + "  Cache status  Signature  Description")
    print("=" * 80)
    for name in sorted(cores.keys()):
        core = cores[name]
        print(
            name.ljust(maxlen)
            + " : "
            + core.cache_status().rjust(10)
            + " : "
            + core.sig_status(trustfile).rjust(8)
            + " : "
            + (core.get_description() or "<No description>")
        )


def list_tools(fs, args):
    from edalize.edatool import get_edatool, walk_tool_packages

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


def gen_list(fs, args):
    cores = fs.get_generators()
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
                        generator_data.get("description", "<No description>"),
                    )
                )


def gen_show(fs, args):
    cores = fs.get_generators()
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


def core_info(fs, args):
    core = _get_core(fs, args.core)
    trustfile = fs.config.ssh_trustfile or args.ssh_trustfile
    print(core.info(trustfile))


def core_sign(fs, args):
    core = _get_core(fs, args.core)
    logger.info("sign core file: " + core.core_file)
    logger.info("with key file: " + args.keyfile)
    sigfile = core.core_file + ".sig"
    logger.info("put result in: " + sigfile)
    sig = signature.sign(core, args.keyfile, None)
    file = open(sigfile, "w")
    file.write(sig)
    file.close()
    print(f"{sigfile} created")


def gen_clean(fs, args):
    cachedir = os.path.join(fs.config.cache_root, "generator_cache")
    shutil.rmtree(cachedir, ignore_errors=True)
    print(f"Cleaned generator cache: {cachedir}")


def run(fs, args):
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

    fs.cm.db.mapping_set(args.mapping)

    if args.lockfile is not None:
        try:
            fs.cm.db.load_lockfile(args.lockfile)
        except SyntaxError as e:
            logger.error(f"Failed to load lock file, {str(e)}")
            exit(1)

    core = _get_core(fs, args.system)

    try:
        flags = dict(core.get_flags(flags["target"]), **flags)
    except SyntaxError as e:
        logger.error(str(e))
        exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)

    # Unconditionally clean out the work root on fresh builds
    # if we use the old tool API or clean flag is set
    if do_configure and (not core.get_flow(flags) or args.clean):
        try:
            prepare_work_root(fs.get_work_root(core, flags))
        except RuntimeError as e:
            logger.error(e)
            exit(1)

    # Frontend/backend separation

    try:
        edam_file, backend = fs.get_backend(core, flags, args.backendargs)

    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except FileNotFoundError as e:
        logger.error(f'Could not find EDA API file "{e.filename}"')
        exit(1)

    makefile = os.path.join(backend.work_root, "Makefile")
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


def config(fs, args):
    conf = Config(path=args.config if args.config else None)

    if not hasattr(conf, args.key):
        logger.error(f"Invalid config parameter: {args.key}")
        exit(1)

    if not args.value:
        # Read
        if hasattr(conf, args.key):
            print(getattr(conf, args.key))
    else:
        # Write
        if hasattr(conf, args.key):
            setattr(conf, args.key, args.value)
            conf.write()


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


def update(fs, args):
    fs.update_libraries(args.libraries)


class CoreCompleter:
    def __call__(self, parsed_args, **kwargs):
        config = Config(parsed_args.config)
        args_to_config(parsed_args, config)
        fs = Fusesoc(config)
        cores = fs.get_cores()
        return cores


class ToolCompleter:
    def __call__(self, parsed_args, **kwargs):
        from edalize.edatool import get_edatool, walk_tool_packages

        _tp = list(walk_tool_packages())
        tools = []
        for tool_name in _tp:
            try:
                tool_class = get_edatool(tool_name)
                if tool_class.get_doc(0)["description"]:
                    tools += [tool_name]
            # Ignore any misbehaving backends
            except Exception:
                pass
        return tools


class GenCompleter:
    def __call__(self, parsed_args, **kwargs):
        config = Config(parsed_args.config)
        args_to_config(parsed_args, config)
        fs = Fusesoc(config)
        cores = fs.get_generators()
        return cores


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
    parser.add_argument("--ssh-trustfile", help="Override trustfile in fusesoc.conf")

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
    parser_core_show.add_argument(
        "core", help="Name of the core to show"
    ).completer = CoreCompleter()
    parser_core_show.set_defaults(func=core_info)

    parser_core_sign = core_subparsers.add_parser(
        "sign", help="Create user signature for a core"
    )
    parser_core_sign.add_argument(
        "core", help="Name of the core to sign"
    ).completer = CoreCompleter()
    parser_core_sign.add_argument("keyfile", help="File containing ssh private key")
    parser_core_sign.set_defaults(func=core_sign)

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
    parser_core_info.add_argument("core").completer = CoreCompleter()
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
    parser_gen_show.add_argument(
        "generator", help="Name of the generator to show"
    ).completer = GenCompleter()
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
    parser_library_add.add_argument(
        "name",
        nargs="?",
        help="A friendly name  for the library. Defaults to last part of sync-uri if not specified.",
    )
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
        help="The location to store the library into (defaults to fusesoc_libraries/[name] or $XDG_DATA_HOME/[name] when --global is set)",
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
        "--clean",
        action="store_true",
        help="Clean build directory on start",
    )
    parser_run.add_argument(
        "--no-export",
        action="store_true",
        help="Reference source files from their current location instead of exporting to a build tree",
    )
    parser_run.add_argument(
        "--build-root",
        help="Output directory for build. VLNV will be appended (defaults to build/)",
    )
    parser_run.add_argument(
        "--work-root",
        help="Output directory for build. VLNV will not be appended (overrides build-root)",
    )
    parser_run.add_argument(
        "--filter",
        help="Add filter. Can be specified multiple times to add multiple filters",
        action="append",
        default=[],
    )
    parser_run.add_argument("--setup", action="store_true", help="Execute setup stage")
    parser_run.add_argument("--build", action="store_true", help="Execute build stage")
    parser_run.add_argument("--run", action="store_true", help="Execute run stage")
    parser_run.add_argument("--target", help="Override default target")
    parser_run.add_argument(
        "--tool", help="Override default tool for target"
    ).completer = ToolCompleter()
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
    parser_run.add_argument(
        "system", help="Select a system to operate on"
    ).completer = CoreCompleter()
    parser_run.add_argument(
        "backendargs", nargs=argparse.REMAINDER, help="arguments to be sent to backend"
    )
    parser_run.add_argument(
        "--lockfile",
        help="Lockfile file path",
        type=pathlib.Path,
    )
    parser_run.add_argument(
        "--mapping",
        help="The VLNV of a core's mapping to apply.",
        default=[],
        action="append",
    )
    parser_run.set_defaults(func=run)

    # config subparser
    parser_config = subparsers.add_parser(
        "config",
        help="Read/write config default section [" + Config.default_section + "]",
    )
    parser_config.set_defaults(func=config)
    parser_config.add_argument("key", help="Config parameter")
    parser_config.add_argument(
        "value", nargs=argparse.OPTIONAL, help="Config parameter"
    )

    return parser


def parse_args(argv):
    parser = get_parser()

    argcomplete.autocomplete(parser, always_complete_options=False)
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args
    if hasattr(args, "subparser"):
        args.subparser.print_help()
    else:
        parser.print_help()
        return None


def args_to_config(args, config):
    if hasattr(args, "resolve_env_vars_early") and args.resolve_env_vars_early:
        setattr(config, "args_resolve_env_vars_early", args.resolve_env_vars_early)

    if (
        hasattr(args, "allow_additional_properties")
        and args.allow_additional_properties
    ):
        setattr(
            config, "args_allow_additional_properties", args.allow_additional_properties
        )

    if args.verbose:
        setattr(config, "args_verbose", args.verbose)

    if hasattr(args, "no_export") and args.no_export:
        setattr(config, "args_no_export", args.no_export)

    if hasattr(args, "build_root") and args.build_root and len(args.build_root) > 0:
        setattr(config, "args_build_root", args.build_root)

    if hasattr(args, "work_root") and args.work_root and len(args.work_root) > 0:
        setattr(config, "args_work_root", args.work_root)

    if hasattr(args, "cores_root") and args.cores_root and len(args.cores_root) > 0:
        setattr(config, "args_cores_root", args.cores_root)

    if hasattr(args, "system_name") and args.system_name and len(args.system_name) > 0:
        setattr(config, "args_system_name", args.system_name)

    if hasattr(args, "filter"):
        config.args_filters = args.filter


def fusesoc(args):
    Fusesoc.init_logging(args.verbose, args.monochrome, args.log_file)

    config = Config(args.config)
    args_to_config(args, config)
    fs = Fusesoc(config)

    # Run the function
    args.func(fs, args)


def main():
    args = parse_args(sys.argv[1:])
    if not args:
        exit(0)

    logger.debug("Command line arguments: " + str(sys.argv))

    fusesoc(args)


if __name__ == "__main__":
    main()
