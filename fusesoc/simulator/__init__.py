from fusesoc.simulator.icarus import SimulatorIcarus
from fusesoc.simulator.modelsim import Modelsim
from fusesoc.simulator.verilator import Verilator
def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'modelsim':
        return Modelsim(system)
    elif sim == 'verilator':
        return Verilator(system)
    else:
        raise RuntimeError("Unknown simulator '"+sim+"'")
