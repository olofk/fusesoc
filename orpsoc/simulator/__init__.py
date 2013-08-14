from orpsoc.simulator.icarus import SimulatorIcarus
from orpsoc.simulator.modelsim import Modelsim
from orpsoc.simulator.verilator import Verilator
def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'modelsim':
        return Modelsim(system)
    elif sim == 'verilator':
        return Verilator(system)
    else:
        raise Exception
