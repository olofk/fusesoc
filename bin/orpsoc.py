import argparse

import Core, Config, System
from SimulatorFactory import SimulatorFactory
from System import System
import os
import sys
SYSTEM = 'generic'
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    config = Config.Config()

    parser.add_argument('action', choices=['list-systems',
                                           'list-cores',
                                           'sim'],
                        help = 'Select an action from the list above')
    parser.add_argument('--sim', nargs='?', const='icarus', default='icarus')
    parser.add_argument('--system', nargs='?', const='generic', default='generic')
    parser.add_argument('--testcase', nargs=1)
    parser.add_argument('--dry-run', action='store_true')

    p = parser.parse_args()

    systems = config.get_systems()
    cores = config.get_cores()
    
    if p.system in systems:
        system = System(config.get_systems()[p.system],config.cores_root)
    else:
        print("Can not find system " + p.system)
        exit(1)

#    for core in system.get_cores():
#        print('='*5+core+'='*5)
#        for f in system.cores[core].get_rtl_files():
#            print(system.cores[core].get_root() + ' : ' + f)
        
    if p.action == 'list-systems':
        for s in systems:
            print(s)
    elif p.action == 'list-cores':
        for c in cores:
            print(c)
    elif p.action == 'sim':
        sim = SimulatorFactory(p.sim, system)
        sim.prepare()
        if p.testcase:
            sim.run(os.path.join(os.getcwd(), p.testcase))

#    system.setup_cores()
#    for i in os.listdir('.'):
#        if i[-5:] == '.vmem':
#            print("Running " + i)
#            sim.run(os.path.join(os.getcwd(),'or1200-basic.vmem'))


#    core_file = '../cores/or1200/or1200.core'
#    local_core_dir = '../cores_dl/or1200'
#    core = Core.Core(core_file)
#    core.provider.dump_config()
#    core.fetch(local_core_dir)
#    core.patch()
#    core.provider.repo_info()
