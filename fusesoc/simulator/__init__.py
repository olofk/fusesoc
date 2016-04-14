from fusesoc.simulator.ghdl import Ghdl
from fusesoc.simulator.icarus import SimulatorIcarus
from fusesoc.simulator.modelsim import Modelsim
from fusesoc.simulator.verilator import Verilator
from fusesoc.simulator.isim import Isim
from fusesoc.simulator.xsim import Xsim
def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'ghdl':
        return Ghdl(system)
    elif sim == 'modelsim':
        return Modelsim(system)
    elif sim == 'verilator':
        return Verilator(system)
    elif sim == 'isim':
        return Isim(system)
    elif sim == 'xsim':
        return Xsim(system)
    else:
        raise RuntimeError("Unknown simulator '"+sim+"'")
