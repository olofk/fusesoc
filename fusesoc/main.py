#!/usr/bin/env python
import argparse
import os
import platform
import subprocess
import sys
import signal

if sys.version_info[0] >= 3:
    import urllib.request as urllib
    from urllib.error import URLError
    from urllib.error import HTTPError
else:
    import urllib
    from urllib2 import URLError
    from urllib2 import HTTPError

#Check if this is run from a local installation
fusesocdir = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
if os.path.exists(os.path.join(fusesocdir, "fusesoc")):
    sys.path[0:0] = [fusesocdir]
else:
    sys.path[0:0] = ['@pythondir@']

from fusesoc.build import BackendFactory
from fusesoc.config import Config
from fusesoc.coremanager import CoreManager, DependencyError
from fusesoc.simulator import SimulatorFactory
from fusesoc.simulator.verilator import Source
from fusesoc.vlnv import Vlnv
from fusesoc.system import System
from fusesoc.core import Core, OptionSectionMissing
from fusesoc.utils import pr_err, pr_info, pr_warn, Launcher

import logging

logging.basicConfig(filename='fusesoc.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger(__name__)

REPO_NAME = 'orpsoc-cores'
REPO_URI  = 'https://github.com/openrisc/orpsoc-cores'

def _get_core(name, has_system=False):
    core = None
    try:
        core = CoreManager().get_core(Vlnv(name))
    except RuntimeError as e:
        pr_err(str(e))
        exit(1)
    except DependencyError as e:
        pr_err("'" + name + "' or any of its dependencies requires '" + e.value + "', but this core was not found")
        exit(1)
    if has_system and not core.system:
        pr_err("Unable to find .system file for '{}'".format(name))
        exit(1)
    return core

def abort_handler(signal, frame):
        print('');
        pr_info('****************************')
        pr_info('****   FuseSoC aborted  ****')
        pr_info('****************************')
        print('');
        sys.exit(0)

signal.signal(signal.SIGINT, abort_handler)

def build(args):
    core = _get_core(args.system, True)

    try:
        backend = BackendFactory(core)
    except RuntimeError as e:
        pr_err("Failed to build '{}': {}".format(args.system, e))
        exit(1)
    try:
        backend.configure(args.backendargs)
    except RuntimeError as e:
        pr_err(str(e))
        exit(1)
    print('')
    try:
        backend.build(args.backendargs)
    except RuntimeError as e:
        pr_err("Failed to build FPGA: " + str(e))

def pgm(args):
    core = _get_core(args.system, True)

    backend = BackendFactory(core)
    try:
        backend.pgm(args.backendargs)
    except RuntimeError as e:
        pr_err("Failed to program the FPGA: " + str(e))

def fetch(args):
    if args.core:
        cores = CoreManager().get_depends(Vlnv(args.core))
        for core in cores:
             pr_info("Fetching " + str(core.name))
             try:
                 core.setup()
             except URLError as e:
                 pr_err("Problem while fetching '" + str(core.name) + "': " + str(e.reason))
                 exit(1)
             except HTTPError as e:
                 pr_err("Problem while fetching '" + str(core.name) + "': " + str(e.reason))
                 exit(1)
    else:
        pr_err("Can't find core '" + args.core + "'")

def init(args):
    # Fix Python 2.x.
    global input
    try:
        input = raw_input
    except NameError:
        pass

    xdg_data_home = os.environ.get('XDG_DATA_HOME') or \
                     os.path.join(os.path.expanduser('~'), '.local', 'share')
    default_dir = default_dir=os.path.join(xdg_data_home, REPO_NAME)
    prompt = 'Directory to use for {} [{}] : '
    if args.y:
        cores_root = None
    else:
        cores_root = input(prompt.format(REPO_NAME, default_dir))
    if not cores_root:
        cores_root = default_dir
    if os.path.exists(cores_root):
        pr_warn("'{}' already exists".format(cores_root))
        #TODO: Check if it's a valid orspoc-cores repo
    else:
        pr_info("Initializing orpsoc-cores")
        args = ['clone', REPO_URI, cores_root]
        Launcher('git', args).run()

    xdg_config_home = os.environ.get('XDG_CONFIG_HOME') or \
                      os.path.join(os.path.expanduser('~'), '.config')
    config_file = os.path.join(xdg_config_home, 'fusesoc', 'fusesoc.conf')


    if os.path.exists(config_file):
        pr_warn("'{}' already exists".format(config_file))
        #TODO. Prepend cores_root to file if it doesn't exist
    else:
        pr_info("Writing configuration file to '{}'".format(config_file))
        if not os.path.exists(os.path.dirname(config_file)):
            os.makedirs(os.path.dirname(config_file))
        f = open(config_file,'w')
        f.write("[main]\n")
        f.write("cores_root = {}\n".format(cores_root))
    pr_info("FuseSoC is ready to use!")

def list_paths(args):
    cores_root = CoreManager().get_cores_root()
    print("\n".join(cores_root))

def list_cores(args):
    cores = CoreManager().get_cores()
    print("\nAvailable cores:\n")
    if not cores:
        cores_root = CoreManager().get_cores_root()
        if cores_root:
            pr_err("No cores found in "+':'.join(cores_root))
        else:
            pr_err("cores_root is not defined")
        exit(1)
    maxlen = max(map(len,cores.keys()))
    print('Core'.ljust(maxlen) + '   Cache status')
    print("="*80)
    for name in sorted(cores.keys()):
        core = cores[name]
        print(name.ljust(maxlen) + ' : ' + core.cache_status())

def core_info(args):
    core = _get_core(args.core)
    core.info()

def list_systems(args):
    print("Available systems:")
    for system in CoreManager().get_systems():
        print(system)

def system_info(args):
    core = _get_core(args.system, True)
    core.info()
    core.system.info()

def sim(args):
    core = _get_core(args.system)
    if args.sim:
        sim_name = args.sim[0]
    elif core.simulators:
        sim_name = core.simulators[0]
    else:
        pr_err("No simulator was found in '"+ args.system + "' core description")
        logger.error("No simulator was found in '"+ args.system + "' core description")
        exit(1)
    try:
        CoreManager().tool = sim_name
        sim = SimulatorFactory(sim_name, core)
    except DependencyError as e:
        pr_err("'" + args.system + "' or any of its dependencies requires '" + e.value + "', but this core was not found")
        exit(1)
    except OptionSectionMissing as e:
        pr_err("'" + args.system + "' miss a mandatory parameter for " + sim_name + " simulation (" + e.value + ")")
        exit(1)
    except RuntimeError as e:
        pr_err(str(e))
        exit(1)
    if (args.testbench):
        sim.toplevel = args.testbench[0]
    if not args.keep or not os.path.exists(sim.sim_root):
        try:
            sim.configure(args.plusargs)
            print('')
        except RuntimeError as e:
            pr_err("Failed to configure the system")
            pr_err(str(e))
            exit(1)
        try:
            sim.build()
        except Source as e:
            pr_err("'" + e.value + "' source type is not valid. Choose 'C' or 'systemC'")
            exit(1)
        except RuntimeError as e:
            pr_err("Failed to build simulation model")
            pr_err(str(e))
            exit(1)
    if not args.build_only:
        try:
            sim.run(args.plusargs)
        except RuntimeError as e:
            pr_err("Failed to run the simulation")
            pr_err(str(e))

def update(args):
    for root in CoreManager().get_cores_root():
        if os.path.exists(root):
            args = ['-C', root,
                    'config', '--get', 'remote.origin.url']
            repo_root = ""
            try:
                repo_root = subprocess.check_output(['git'] + args).decode("utf-8")
                if repo_root.strip() == REPO_URI:
                    pr_info("Updating '{}'".format(root))
                    args = ['-C', root, 'pull']
                    Launcher('git', args).run()
            except subprocess.CalledProcessError:
                pass

def run(args):
    cm = CoreManager()
    config = Config()

    # Get the environment variable for further cores
    env_cores_root = []
    if os.getenv("FUSESOC_CORES"):
        env_cores_root = os.getenv("FUSESOC_CORES").split(":")
    env_cores_root.reverse()

    for cores_root in [args.cores_root,
                       env_cores_root,
                       config.cores_root,
                       config.systems_root]:
        try:
            cm.add_cores_root(cores_root)
        except (RuntimeError, IOError) as e:
            pr_warn("Failed to register cores root '{}'".format(str(e)))
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
    config.monochrome = vars(args)['monochrome']
    if config.monochrome:
        logger.debug("Monochrome output")
    else:
        logger.debug("Colorful output")
    config.verbose = vars(args)['verbose']
    if config.verbose:
        logger.debug("Verbose output")
    else:
        logger.debug("Concise output")
    # Run the function
    args.func(args)

def main():
    logger.debug("Command line arguments: " + str(sys.argv))
    if os.getenv("FUSESOC_CORES"):
        logger.debug("FUSESOC_CORES: " + str(os.getenv("FUSESOC_CORES").split(':')))

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # Global options
    parser.add_argument('--cores-root', help='Add additional directories containing cores', action='append')
    parser.add_argument('--32', help='Force 32 bit mode for invoked tools', action='store_true')
    parser.add_argument('--64', help='Force 64 bit mode for invoked tools', action='store_true')
    parser.add_argument('--monochrome', help='Don\'t use color for messages', action='store_true')
    parser.add_argument('--verbose', help='More info messages', action='store_true')

    #General options
    parser_build = subparsers.add_parser('build', help='Build an FPGA load module')
    parser_build.add_argument('system')
    parser_build.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_build.set_defaults(func=build)

    parser_init = subparsers.add_parser('init', help='Initialize the FuseSoC core libraries')
    parser_init.add_argument('-y', action='store_true', help='Skip user input and use default settings')
    parser_init.set_defaults(func=init)

    parser_pgm = subparsers.add_parser('pgm', help='Program a FPGA with a system configuration')
    parser_pgm.add_argument('system')
    parser_pgm.add_argument('backendargs', nargs=argparse.REMAINDER)
    parser_pgm.set_defaults(func=pgm)

    parser_fetch = subparsers.add_parser('fetch', help='Fetch a remote core and its dependencies to local cache')
    parser_fetch.add_argument('core')
    parser_fetch.set_defaults(func=fetch)

    parser_list_systems = subparsers.add_parser('list-systems', help='List available systems')
    parser_list_systems.set_defaults(func=list_systems)

    parser_system_info = subparsers.add_parser('system-info', help='Displays details about a system')
    parser_system_info.add_argument('system')
    parser_system_info.set_defaults(func=system_info)

    parser_list_cores = subparsers.add_parser('list-cores', help='List available cores')
    #parser_list_cores.
    parser_list_cores.set_defaults(func=list_cores)

    parser_core_info = subparsers.add_parser('core-info', help='Displays details about a core')
    parser_core_info.add_argument('core')
    parser_core_info.set_defaults(func=core_info)

    parser_list_paths = subparsers.add_parser('list-paths', help='Displays the search order for core root paths')
    parser_list_paths.set_defaults(func=list_paths)

    #Simulation subparser
    parser_sim = subparsers.add_parser('sim', help='Setup and run a simulation')
    parser_sim.add_argument('--sim', nargs=1, help='Override the simulator settings from the system file')
    parser_sim.add_argument('--build-only', action='store_true', help='Build the simulation binary without running the simulator')
    parser_sim.add_argument('--force', action='store_true', help='Force rebuilding simulation model when directory exists')
    parser_sim.add_argument('--keep', action='store_true', help='Prevent rebuilding simulation model if it exists')
    parser_sim.add_argument('--dry-run', action='store_true')
    parser_sim.add_argument('--testbench', nargs=1, help='Override default testbench')
    parser_sim.add_argument('system',help='Select a system to simulate') #, choices = Config().get_systems())
    parser_sim.add_argument('plusargs', nargs=argparse.REMAINDER)
    parser_sim.set_defaults(func=sim)

    parser_update = subparsers.add_parser('update', help='Update the FuseSoC core libraries')
    parser_update.set_defaults(func=update)

    parsed_args = parser.parse_args()
    if hasattr(parsed_args, 'func'):
        run(parsed_args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
