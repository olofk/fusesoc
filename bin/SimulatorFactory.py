from SimulatorIcarus import SimulatorIcarus

#class SimulatorFactory:
    #def __init__(self, sim):
def SimulatorFactory(sim,system, config):
    if sim == 'icarus':
        return SimulatorIcarus(system, config)
    elif sim == 'modelsim':
        return SimulatorModelsim()
    else:
        raise Exception
        
