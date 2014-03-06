from fusesoc.simulator.icarus import SimulatorIcarus
from fusesoc.simulator.modelsim import Modelsim
from fusesoc.simulator.verilator import SimulatorVerilator
def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'modelsim':
        return Modelsim(system)
    elif sim == 'verilator':
        return SimulatorVerilator(system)
    else:
        raise Exception
