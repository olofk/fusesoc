#!/usr/bin/python
import argparse

from orpsoc.build import BackendFactory
from orpsoc.config import Config
from orpsoc.simulator import SimulatorFactory
from orpsoc.system import System
from orpsoc.core import Core
import os

def build(args):
    system_file = Config().get_systems()[args.system]
    system = System(system_file)

    backend = BackendFactory(system)
    backend.configure()
    backend.build()
    
def list_cores(args):
    cores = Config().get_cores()
    print("Available cores:")
    for core in cores:
        print(core + ' : ' + Core(cores[core]).cache_status())

def list_systems(args):
    print("Available systems:")
    for system in Config().get_systems():
        print(system)

def sim(args):
    system_file = Config().get_systems()[args.system]
    system = System(system_file)

    if args.sim:
        sim_name = args.sim[0]
    else:
        sim_name = system.simulators[0]
    sim = SimulatorFactory(sim_name, system)
    sim.configure()
    sim.build()
    if args.testcase:
        print("Running test case: " + args.testcase[0])
        sim.run(args)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    #General options
    parser_build = subparsers.add_parser('build', help='Build an FPGA load module')
    parser_build.add_argument('system')
    parser_build.set_defaults(func=build)

    parser_list_systems = subparsers.add_parser('list-systems', help='List available systems')
    parser_list_systems.set_defaults(func=list_systems)

    parser_list_cores = subparsers.add_parser('list-cores', help='List available cores')
    #parser_list_cores.
    parser_list_cores.set_defaults(func=list_cores)

    #Simulation subparser
    parser_sim = subparsers.add_parser('sim', help='Setup and run a simulation')
    parser_sim.add_argument('--sim', nargs=1)
    parser_sim.add_argument('--testcase', nargs=1)
    parser_sim.add_argument('--timeout', type=int, nargs=1)
    parser_sim.add_argument('--enable-dbg', action='store_true')
    parser_sim.add_argument('--dry-run', action='store_true')
    parser_sim.add_argument('system')
    parser_sim.set_defaults(func=sim)

    p = parser.parse_args()
    p.func(p)
