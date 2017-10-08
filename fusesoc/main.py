#!/usr/bin/env python
import argparse
import importlib
import os
import platform
import shutil
import subprocess
import sys
import signal
import yaml

from fusesoc import __version__

#Check if this is run from a local installation
fusesocdir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
if os.path.exists(os.path.join(fusesocdir, "fusesoc")):
    sys.path[0:0] = [fusesocdir]
else:
    sys.path[0:0] = ['@pythondir@']

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager, DependencyError
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

def _get_core(name):
    core = None
    try:
        core = CoreManager().get_core(Vlnv(name))
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)
    except DependencyError as e:
        logger.error("'" + name + "' or any of its dependencies requires '" + e.value + "', but this core was not found")
        exit(1)
    return core

def _import(name):
    module = importlib.import_module('fusesoc.edatools.{}'.format(name))
    return getattr(module, name.capitalize())

def abort_handler(signal, frame):
        print('');
        logger.info('****************************')
        logger.info('****   FuseSoC aborted  ****')
        logger.info('****************************')
        print('');
        sys.exit(0)

signal.signal(signal.SIGINT, abort_handler)

def build(args):
    do_configure = True
    do_build = not args.setup
    do_run = False
    flags = {'target' : 'synth',
             'tool' : None,}
    run_backend(not args.no_export,
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def pgm(args):
    do_configure = False
    do_build = False
    do_run = True
    flags = {'target' : 'synth',
             'tool' : None}
    run_backend('build',
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def fetch(args):
    core = _get_core(args.core)

    try:
        core.setup()
    except RuntimeError as e:
        logger.error("Failed to fetch '{}': {}".format(core.name, str(e)))
        exit(1)

def init(args):
    # Fix Python 2.x.
    global input
    try:
        input = raw_input
    except NameError:
        pass

    xdg_data_home = os.environ.get('XDG_DATA_HOME') or \
                    os.path.join(os.path.expanduser('~'),
                                 '.local', 'share', 'fusesoc')
    _repo_paths = []
    for repo in REPOS:
        default_dir = os.path.join(xdg_data_home, repo[0])
        prompt = 'Directory to use for {} ({}) [{}] : '
        if args.y:
            cores_root = None
        else:
            cores_root = input(prompt.format(repo[0], repo[2], default_dir))
        if not cores_root:
            cores_root = default_dir
        if os.path.exists(cores_root):
            logger.warning("'{}' already exists".format(cores_root))
            #TODO: Prompt for overwrite
        else:
            _repo_paths.append(cores_root)
            logger.info("Initializing {}".format(repo[0]))
            git_args = ['clone', repo[1], cores_root]
            try:
                Launcher('git', git_args).run()
            except RuntimeError as e:
                logger.error("Init failed: " + str(e))
                exit(1)

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
                      os.path.join(os.path.expanduser('~'), '.config')
    config_file = os.path.join(xdg_config_home, 'fusesoc', 'fusesoc.conf')


    if os.path.exists(config_file):
        logger.warning("'{}' already exists".format(config_file))
        #TODO. Prepend cores_root to file if it doesn't exist
    else:
        logger.info("Writing configuration file to '{}'".format(config_file))
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))
        f = open(config_file,'w')
        f.write("[main]\n")
        f.write("cores_root = {}\n".format(' '.join(_repo_paths)))
    logger.info("FuseSoC is ready to use!")

def list_paths(args):
    cores_root = CoreManager().get_cores_root()
    print("\n".join(cores_root))

def list_cores(args):
    cores = CoreManager().get_cores()
    print("\nAvailable cores:\n")
    if not cores:
        cores_root = CoreManager().get_cores_root()
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

def core_info(args):
    core = _get_core(args.core)
    print(core.info())

def list_systems(args):
    print("Available systems:")
    for core in CoreManager().get_cores().values():
        if core.get_tool({'target' : 'synth', 'tool' : None}):
            print(str(core.name))

def run_backend(export, do_configure, do_build, do_run, flags, system, backendargs):
    tool_error = "No tool was supplied on command line or found in '{}' core description"
    core = _get_core(system)
    tool = core.get_tool(flags)
    if not tool:
        logger.error(tool_error.format(system))
        exit(1)
    flags['tool'] = tool
    if export:
        export_root = os.path.join(Config().build_root, core.name.sanitized_name, 'src')
    else:
        export_root = None
    work_root   = os.path.join(Config().build_root,
                               core.name.sanitized_name,
                               core.get_work_root(flags))
    eda_api_file = os.path.join(work_root,
                                core.name.sanitized_name+'.eda.yml')
    if do_configure:
        if os.path.exists(work_root):
            for f in os.listdir(work_root):
                if os.path.isdir(os.path.join(work_root, f)):
                    shutil.rmtree(os.path.join(work_root, f))
                else:
                    os.remove(os.path.join(work_root, f))
        else:
            os.makedirs(work_root)
        try:
            eda_api = CoreManager().setup(core.name,
                                          flags,
                                          work_root=work_root,
                                          export_root=export_root)
        except DependencyError as e:
            logger.error(e.msg + "\nFailed to resolve dependencies for {}".format(system))
            exit(1)
        except SyntaxError as e:
            logger.error(e.msg)
            exit(1)
        with open(eda_api_file,'w') as f:
            f.write(yaml.dump(eda_api))

    #Frontend/backend separation

    try:
        backend = _import(tool)(eda_api_file=eda_api_file, work_root=work_root)
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

def sim(args):
    do_configure = not args.keep
    do_build = not args.setup
    do_run   = not (args.build_only or args.setup)
    
    flags = {'flow' : 'sim',
             'tool' : args.sim,
             'target' : 'sim',
             'testbench' : args.testbench
    }
    run_backend(not args.no_export,
                do_configure, do_build, do_run,
                flags, args.system, args.backendargs)

def update(args):
    for root in CoreManager().get_cores_root():
        if os.path.exists(root):
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

def run(args):
    level = logging.DEBUG if args.verbose else logging.INFO

    setup_logging(level=level, monchrome=args.monochrome)
    logger.debug("Command line arguments: " + str(sys.argv))
    if os.getenv("FUSESOC_CORES"):
        logger.debug("FUSESOC_CORES: " + str(os.getenv("FUSESOC_CORES").split(':')))
    if args.verbose:
        logger.debug("Verbose output")
    else:
        logger.debug("Concise output")

    if args.monochrome:
        logger.debug("Monochrome output")
    else:
        logger.debug("Colorful output")

    cm = CoreManager()
    config = Config()

    # Get the environment variable for further cores
    env_cores_root = []
    if os.getenv("FUSESOC_CORES"):
        env_cores_root = os.getenv("FUSESOC_CORES").split(":")
    env_cores_root.reverse()

    for cores_root in [config.cores_root,
                       config.systems_root,
                       env_cores_root,
                       args.cores_root]:
        try:
            cm.add_cores_root(cores_root)
        except (RuntimeError, IOError) as e:
            logger.warning("Failed to register cores root '{}'".format(str(e)))
    # Process global options
    if vars(args)['32']:
        config.archbits = 32
        logger.debug("Forcing 32-bit mode")
    elif vars(args)['64']:
        config.archbits = 64
        logger.debug("Forcing 64-bit mode")
    else:
        config.archbits = 64 if platform.architecture()[0] == '64bit' else 32
        logger.debug("Autodetected " + str(config.archbits) + "-bit mode")
    if sys.platform == "win32":
        config.cygpath = vars(args)['cygpath']
        if config.cygpath:
            logger.debug("Using cygpath translation")
        else:
            logger.debug("Using native Windows paths")
    # Run the function
    args.func(args)

def main():

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global actions
    parser.add_argument('--version', help='Display the FuseSoC version', action='version', version=__version__)

    # Global options
    parser.add_argument('--cores-root', help='Add additional directories containing cores', action='append')
    parser.add_argument('--32', help='Force 32 bit mode for invoked tools', action='store_true')
    parser.add_argument('--64', help='Force 64 bit mode for invoked tools', action='store_true')
    parser.add_argument('--monochrome', help='Don\'t use color for messages', action='store_true')
    parser.add_argument('--verbose', help='More info messages', action='store_true')
    parser.add_argument('--cygpath', help='Use POSIX paths on Windows (no effect on POSIX systems)', action='store_true')

    # build subparser
    parser_build = subparsers.add_parser('build', help='Build an FPGA load module')
    parser_build.add_argument('--no-export', action='store_true', help='Reference source files from their current location instead of exporting to a build tree')
    parser_build.add_argument('--setup', action='store_true', help='Only create the project files without running the EDA tool')
    parser_build.add_argument('--target', help='Override default target')
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

    # list-systems subparser
    parser_list_systems = subparsers.add_parser('list-systems', help='List available systems')
    parser_list_systems.set_defaults(func=list_systems)

    # list-cores subparser
    parser_list_cores = subparsers.add_parser('list-cores', help='List available cores')
    parser_list_cores.set_defaults(func=list_cores)

    # core-info subparser
    parser_core_info = subparsers.add_parser('core-info', help='Display details about a core')
    parser_core_info.add_argument('core')
    parser_core_info.set_defaults(func=core_info)

    # list-paths subparser
    parser_list_paths = subparsers.add_parser('list-paths', help='Display the search order for core root paths')
    parser_list_paths.set_defaults(func=list_paths)

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
    parser_sim.add_argument('system', help='Select a system to simulate') #, choices = Config().get_systems())
    parser_sim.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_sim.set_defaults(func=sim)

    # update subparser
    parser_update = subparsers.add_parser('update', help='Update the FuseSoC core libraries')
    parser_update.set_defaults(func=update)

    parsed_args = parser.parse_args()
    if hasattr(parsed_args, 'func'):
        run(parsed_args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
