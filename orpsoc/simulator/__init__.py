from orpsoc.simulator.icarus import SimulatorIcarus

def SimulatorFactory(sim,system):
    if sim == 'icarus':
        return SimulatorIcarus(system)
    elif sim == 'modelsim':
        return SimulatorModelsim()
    else:
        raise Exception
