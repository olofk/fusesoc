#!/usr/bin/env python
import argparse
import os
import subprocess
import sys
import signal

from fusesoc import __version__

#Check if this is run from a local installation
fusesocdir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
if os.path.exists(os.path.join(fusesocdir, "fusesoc")):
    sys.path[0:0] = [fusesocdir]

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager, DependencyError
from fusesoc.edalizer import Edalizer
from edalize import get_edatool
from fusesoc.provider import get_provider
from fusesoc.vlnv import Vlnv
from fusesoc.utils import Launcher, setup_logging

import logging

logger = logging.getLogger(__name__)

REPOS = [('orpsoc-cores',
          'https://github.com/openrisc/orpsoc-cores',
          "old base library"),
         ('fusesoc-cores',
          'https://github.com/fusesoc/fusesoc-cores',
          "new base library")]

def _get_core(cm, name):
    core = None
    try:
        core = cm.get_core(Vlnv(name))
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except DependencyError as e:
        logger.error("'" + name + "' or any of its dependencies requires '" + e.value + "', but this core was not found")
        exit(1)
    return core

def abort_handler(signal, frame):
        print('');
        logger.info('****************************')
        logger.info('****   FuseSoC aborted  ****')
        logger.info('****************************')
        print('');
        sys.exit(0)

signal.signal(signal.SIGINT, abort_handler)

def build(cm, args):
    do_configure = True
    do_build = not args.setup
    do_run = False
    if not args.target:
        target = 'synth'
    else:
        target = args.target
    flags = {'target' : target,
             'tool' : args.tool}
    run_backend(cm, not args.no_export,
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def pgm(cm, args):
    do_configure = False
    do_build = False
    do_run = True
    flags = {'target' : 'synth',
             'tool' : None}
    run_backend(cm, 'build',
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def fetch(cm, args):
    core = _get_core(cm, args.core)

    try:
        core.setup()
    except RuntimeError as e:
        logger.error("Failed to fetch '{}': {}".format(core.name, str(e)))
        exit(1)

def init(cm, args):
    # Fix Python 2.x.
    global input
    try:
        input = raw_input
    except NameError:
        pass

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
                      os.path.join(os.path.expanduser('~'), '.config')
    config_file = os.path.join(xdg_config_home, 'fusesoc', 'fusesoc.conf')


    if os.path.exists(config_file):
        logger.warning("'{}' already exists".format(config_file))
        #TODO. Prepend cores_root to file if it doesn't exist
        f = open(config_file, 'w+')
    else:
        logger.info("Writing configuration file to '{}'".format(config_file))
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))
        f = open(config_file,'w+')

    config = Config(file=f)

    xdg_data_home = os.environ.get('XDG_DATA_HOME') or \
             os.path.join(os.path.expanduser('~'), '.local/share')
    _repo_paths = []
    for repo in REPOS:
        name = repo[0]
        library = {
                'sync-uri': repo[1],
                'sync-type': 'git'
                }

        default_dir = os.path.join(xdg_data_home, name)
        prompt = 'Directory to use for {} ({}) [{}] : '
        if args.y:
            location = None
        else:
            location = input(prompt.format(repo[0], repo[2], default_dir))
        if location:
            library['location'] = location
        else:
            location = default_dir
        if os.path.exists(location):
            logger.warning("'{}' already exists".format(location))
            #TODO: Prompt for overwrite
        else:
            logger.info("Initializing {}".format(name))
            try:
                config.add_library(name, library)
            except RuntimeError as e:
                logger.error("Init failed: " + str(e))
                exit(1)
    logger.info("FuseSoC is ready to use!")

def list_paths(cm, args):
    cores_root = cm.get_cores_root()
    print("\n".join(cores_root))

def add_library(cm, args):
    library = {}
    name = args.name
    sync_uri = vars(args)['sync-uri']
    if 'sync-type' in vars(args):
        provider = vars(args)['sync-type']
        library['sync-type'] = provider
    elif os.path.isdir(sync_uri):
        provider = 'local'
        library['sync-type'] = provider
    else:
        provider = 'git'

    if provider == 'local' and not args.location:
        logger.info("Interpreting sync-uri '{}' as location for local provider.".format(sync_uri))
        library['location'] = os.path.abspath(sync_uri)
        library['sync-type'] = 'local'
    elif provider == 'local' and os.path.abspath(args.location) != os.path.abspath(sync_uri):
        logger.error("Location '{}' does not match sync-uri '{}' for local provider. Consider specifying only sync-uri.".format(args.location, sync_uri))
        exit(1)
    else:
        library['sync-uri'] = sync_uri
        if args.location:
            library['location'] = os.path.abspath(args.location)
    if args.no_auto_sync:
        library['auto-sync'] = False

    if args.config:
        config = Config(file=args.config)
    elif vars(args)['global']:
        xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
                          os.path.join(os.path.expanduser('~'), '.config')
        config_file = os.path.join(xdg_config_home, 'fusesoc', 'fusesoc.conf')
        config = Config(path=config_file)
    else:
        config = Config(path="fusesoc.conf")

    try:
        config.add_library(name, library)
    except RuntimeError as e:
        logger.error("`add library` failed: " + str(e))
        exit(1)


def list_cores(cm, args):
    cores = cm.get_cores()
    print("\nAvailable cores:\n")
    if not cores:
        cores_root = cm.get_cores_root()
        if cores_root:
            logger.error("No cores found in "+':'.join(cores_root))
        else:
            logger.error("cores_root is not defined")
        exit(1)
    maxlen = max(map(len,cores.keys()))
    print('Core'.ljust(maxlen) + '   Cache status')
    print("="*80)
    for name in sorted(cores.keys()):
        core = cores[name]
        print(name.ljust(maxlen) + ' : ' + core.cache_status())

def gen_list(cm, args):
    cores = cm.get_generators()
    print("\nAvailable generators:\n")
    maxlen = max(map(len,cores.keys()))
    print('Core'.ljust(maxlen) + '   Generator')
    print("="*(maxlen+12))
    for core in sorted(cores.keys()):
        for generator_name, generator_data in cores[core].items():
            print('{} : {} : {}'.format(core.ljust(maxlen), generator_name, generator_data.description or "<No description>"))

def gen_show(cm, args):
    cores = cm.get_generators()
    for core in sorted(cores.keys()):
        for generator_name, generator_data in cores[core].items():
            if generator_name == args.generator:
                print("""
Core        : {}
Generator   : {}
Description : {}
Usage       :

{}""".format(core, generator_name, generator_data.description or "<No description>", generator_data.usage or ""))

def core_info(cm, args):
    core = _get_core(cm, args.core)
    print(core.info())

def run(cm, args):
    stages = (args.setup, args.build, args.run)
    #Run all stages by default if no stage flags are set
    if  stages == (False, False, False):
        do_configure = True
        do_build     = True
        do_run       = True
    elif stages == (True, False, True):
        logger.error("Configure and run without build is invalid")
        exit(1)
    else:
        do_configure = args.setup
        do_build     = args.build
        do_run       = args.run

    flags = {'tool'   : args.tool,
             'target' : args.target}
    run_backend(cm,
                not args.no_export,
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)


def run_backend(cm, export, do_configure, do_build, do_run, flags, system, backendargs):
    tool_error = "No tool was supplied on command line or found in '{}' core description"
    core = _get_core(cm, system)
    try:
        tool = core.get_tool(flags)
    except SyntaxError as e:
        logger.error(str(e))
        exit(1)
    if not tool:
        logger.error(tool_error.format(system))
        exit(1)
    flags['tool'] = tool
    if export:
        export_root = os.path.join(cm.config.build_root, core.name.sanitized_name, 'src')
    else:
        export_root = None
    try:
        work_root   = os.path.join(cm.config.build_root,
                                   core.name.sanitized_name,
                                   core.get_work_root(flags))
    except SyntaxError as e:
        logger.error(e.msg)
        exit(1)
    eda_api_file = os.path.join(work_root,
                                core.name.sanitized_name+'.eda.yml')
    if do_configure:
        try:
            cores = cm.get_depends(core.name, flags)
        except DependencyError as e:
            logger.error(e.msg + "\nFailed to resolve dependencies for {}".format(system))
            exit(1)
        try:
            edalizer = Edalizer(core.name,
                                flags,
                                cores,
                                cache_root=cm.config.cache_root,
                                work_root=work_root,
                                export_root=export_root)
        except SyntaxError as e:
            logger.error(e.msg)
            exit(1)
        except RuntimeError as e:
            logger.error("Setup failed : {}".format(str(e)))
            exit(1)
        edalizer.to_yaml(eda_api_file)

    #Frontend/backend separation

    try:
        backend = get_edatool(tool)(eda_api=edalizer.edalize,
                                    work_root=work_root)
    except ImportError:
        logger.error('Backend "{}" not found'.format(tool))
        exit(1)
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except FileNotFoundError as e:
        logger.error('Could not find EDA API file "{}"'.format(e.filename))
        exit(1)

    if do_configure:
        try:
            backend.configure(backendargs)
            print('')
        except RuntimeError as e:
            logger.error("Failed to configure the system")
            logger.error(str(e))
            exit(1)

    if do_build:
        try:
            backend.build()
        except RuntimeError as e:
            logger.error("Failed to build {} : {}".format(str(core.name),
                                                          str(e)))
            exit(1)

    if do_run:
        try:
            backend.run(backendargs)
        except RuntimeError as e:
            logger.error("Failed to run {} : {}".format(str(core.name),
                                                        str(e)))
            exit(1)

def sim(cm, args):
    do_configure = not args.keep
    do_build = not (args.setup or args.keep)
    do_run   = not (args.build_only or args.setup)

    flags = {'flow' : 'sim',
             'tool' : args.sim,
             'target' : 'sim',
             'testbench' : args.testbench
    }
    run_backend(cm, not args.no_export,
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def update(cm, args):
    libraries = args.libraries
    for root in cm.get_cores_root():
        if not root in cm.config.cores_root:
            # This is a library - handled differently
            continue
        if os.path.exists(root) and (not libraries or root in libraries):
            args = ['-C', root,
                    'config', '--get', 'remote.origin.url']
            repo_root = ""
            try:
                repo_root = subprocess.check_output(['git'] + args).decode("utf-8")
                if repo_root.strip() in [repo[1] for repo in REPOS]:
                    logger.info("Updating '{}'".format(root))
                    args = ['-C', root, 'pull']
                    Launcher('git', args).run()
            except subprocess.CalledProcessError:
                pass

    for (name, library) in cm.config.libraries.items():
        # TODO I don't like this huge "if", get rid of it
        if os.path.exists(library['location']) and \
                not library['sync-uri'] is None and \
                (name in libraries or \
                library['location'] in libraries or \
                library['auto-sync']):
            logger.info("Updating '{}'".format(name))
            try:
                provider = get_provider(library['sync-type'])
            except ImportError as e:
                logger.error("Invalid sync-type '{}' for library '{}' - skipping".format(library['sync-type'], name))
                continue
            try:
                provider.update_library(library)
            except RuntimeError as e:
                logger.error("Failed to update library: " + str(e) + ". Continuing...")

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

def init_coremanager(config, args_cores_root):
    logger.debug("Command line arguments: " + str(sys.argv))

    if os.getenv("FUSESOC_CORES"):
        logger.debug("FUSESOC_CORES: " + str(os.getenv("FUSESOC_CORES").split(':')))
    cm = CoreManager(config)

    # Get the environment variable for further cores
    env_cores_root = []
    if os.getenv("FUSESOC_CORES"):
        env_cores_root = os.getenv("FUSESOC_CORES").split(":")
    env_cores_root.reverse()

    core_libraries = [l['location'] for l in config.libraries.values()]
    for cores_root in config.cores_root + \
                       [config.systems_root] + \
                       env_cores_root + \
                       core_libraries + \
                       args_cores_root:
        try:
            cm.add_cores_root(cores_root)
        except (RuntimeError, IOError) as e:
            logger.warning("Failed to register cores root '{}'".format(str(e)))

    return cm

def parse_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global actions
    parser.add_argument('--version', help='Display the FuseSoC version', action='version', version=__version__)

    # Global options
    parser.add_argument('--cores-root', help='Add additional directories containing cores', default=[], action='append')
    parser.add_argument('--config', help='Specify the config file to use', type=argparse.FileType('r'))
    parser.add_argument('--monochrome', help='Don\'t use color for messages', action='store_true', default=not sys.stdout.isatty())
    parser.add_argument('--verbose', help='More info messages', action='store_true')
    parser.add_argument('--log-file', help='Write log messages to file')

    # build subparser
    parser_build = subparsers.add_parser('build', help='Build an FPGA load module')
    parser_build.add_argument('--no-export', action='store_true', help='Reference source files from their current location instead of exporting to a build tree')
    parser_build.add_argument('--setup', action='store_true', help='Only create the project files without running the EDA tool')
    parser_build.add_argument('--target', help='Override default target')
    parser_build.add_argument('--tool', help='Override default tool for target')
    parser_build.add_argument('system')
    parser_build.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_build.set_defaults(func=build)

    # init subparser
    parser_init = subparsers.add_parser('init', help='Initialize the FuseSoC core libraries')
    parser_init.add_argument('-y', action='store_true', help='Skip user input and use default settings')
    parser_init.set_defaults(func=init)

    # pgm subparser
    parser_pgm = subparsers.add_parser('pgm', help='Program an FPGA with a system configuration')
    parser_pgm.add_argument('system')
    parser_pgm.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_pgm.set_defaults(func=pgm)

    # fetch subparser
    parser_fetch = subparsers.add_parser('fetch', help='Fetch a remote core and its dependencies to local cache')
    parser_fetch.add_argument('core')
    parser_fetch.set_defaults(func=fetch)

    # list-cores subparser
    parser_list_cores = subparsers.add_parser('list-cores', help='List available cores')
    parser_list_cores.set_defaults(func=list_cores)

    # core-info subparser
    parser_core_info = subparsers.add_parser('core-info', help='Display details about a core')
    parser_core_info.add_argument('core')
    parser_core_info.set_defaults(func=core_info)

    # gen subparser
    parser_gen = subparsers.add_parser('gen', help='Run or show information about generators')
    gen_subparsers = parser_gen.add_subparsers()

    # gen list subparser
    parser_gen_list = gen_subparsers.add_parser('list', help='List available generators')
    parser_gen_list.set_defaults(func=gen_list)

    # gen show subparser
    parser_gen_show = gen_subparsers.add_parser('show', help='Show information about a generator')
    parser_gen_show.add_argument('generator', help='Name of the generator to show')
    parser_gen_show.set_defaults(func=gen_show)

    # list-paths subparser
    parser_list_paths = subparsers.add_parser('list-paths', help='Display the search order for core root paths')
    parser_list_paths.set_defaults(func=list_paths)

    # library subparser
    parser_library = subparsers.add_parser('library', help='Subcommands for dealing with library management')
    library_subparsers = parser_library.add_subparsers()

    # library add subparser
    parser_library_add = library_subparsers.add_parser('add', help='Add new library to fusesoc.conf')
    parser_library_add.add_argument('name', help='A friendly name  for the library')
    parser_library_add.add_argument('sync-uri', help='The URI source for the library (can be a file system path)')
    parser_library_add.add_argument('--location', help='The location to store the library into (defaults to $XDG_DATA_HOME/[name])')
    parser_library_add.add_argument('--sync-type', help="The provider type for the library. Defaults to 'git'.", choices=['git', 'local'])
    parser_library_add.add_argument('--no-auto-sync', action='store_true', help='Disable automatic updates of the library')
    parser_library_add.add_argument('--global', action='store_true', help='Use the global FuseSoc config file in $XDG_CONFIG_HOME/fusesoc/fusesoc.conf')
    parser_library_add.set_defaults(func=add_library)

    # run subparser
    parser_run = subparsers.add_parser('run', help="Start a tool flow")
    parser_run.add_argument('--no-export', action='store_true', help='Reference source files from their current location instead of exporting to a build tree')
    parser_run.add_argument('--setup',  action='store_true', help="Execute setup stage")
    parser_run.add_argument('--build',  action='store_true', help="Execute build stage")
    parser_run.add_argument('--run'  ,  action='store_true', help="Execute run stage")
    parser_run.add_argument('--target', help='Override default target')
    parser_run.add_argument('--tool', help="Override default tool for target")
    parser_run.add_argument('system', help='Select a system to operate on')
    parser_run.add_argument('backendargs', nargs=argparse.REMAINDER, help="arguments to be sent to backend")
    parser_run.set_defaults(func=run)

    # sim subparser
    parser_sim = subparsers.add_parser('sim', help='Setup and run a simulation')
    parser_sim.add_argument('--no-export', action='store_true', help='Reference source files from their current location instead of exporting to a build tree')
    parser_sim.add_argument('--sim', help='Override the simulator settings from the system file')
    parser_sim.add_argument('--setup', action='store_true', help='Only create the project files without running the EDA tool')
    parser_sim.add_argument('--build-only', action='store_true', help='Build the simulation binary without running the simulator')
    parser_sim.add_argument('--force', action='store_true', help='Force rebuilding simulation model when directory exists')
    parser_sim.add_argument('--keep', action='store_true', help='Prevent rebuilding simulation model if it exists')
    parser_sim.add_argument('--target', help='Override default target')
    parser_sim.add_argument('--testbench', help='Override default testbench')
    parser_sim.add_argument('system', help='Select a system to simulate')
    parser_sim.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_sim.set_defaults(func=sim)

    # update subparser
    parser_update = subparsers.add_parser('update', help='Update the FuseSoC core libraries')
    parser_update.add_argument('libraries', nargs='*', help='The libraries (or core roots) to update (defaults to all)')
    parser_update.set_defaults(func=update)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        return args
    else:
        parser.print_help()
        return None

def main():

    args = parse_args()
    if not args:
        exit(0)

    init_logging(args.verbose, args.monochrome, args.log_file)
    config = Config(file=args.config)
    cm = init_coremanager(config, args.cores_root)

    # Run the function
    args.func(cm, args)

if __name__ == "__main__":
    main()
