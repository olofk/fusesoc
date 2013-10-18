from orpsoc.build.quartus import Quartus

def BackendFactory(system):
    if system.backend_name == 'quartus':
        return Quartus(system)
    else:
        raise Exception("Backend not found")
