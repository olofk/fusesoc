from orpsoc.simulator.icarus import SimulatorIcarus
from orpsoc.simulator.modelsim import Modelsim
def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'modelsim':
        return Modelsim(system)
    else:
        raise Exception
