#!/usr/bin/python
import argparse

from orpsoc.config import Config
from orpsoc.simulator import SimulatorFactory
from orpsoc.system import System
from orpsoc.core import Core
import os

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
    if not args.sim:
        args.sim=['icarus']
    system_file = Config().get_systems()[args.system]
    system = System(system_file)

    sim = SimulatorFactory(args.sim[0], system)
    sim.prepare()
    if args.testcase:
        print("Running test case: " + args.testcase[0])
        sim.run(args)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    #General options
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
