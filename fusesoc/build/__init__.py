from fusesoc.build.quartus import Quartus
from fusesoc.build.ise import Ise
from fusesoc.build.icestorm import Icestorm
from fusesoc.build.vivado import Vivado

def BackendFactory(system):
    backend = system.system.backend_name
    if backend == 'quartus':
        return Quartus(system)
    elif backend == 'ise':
        return Ise(system)
    elif backend == 'icestorm':
        return Icestorm(system)
    elif backend == 'vivado':
        return Vivado(system)
    else:
        raise RuntimeError('Backend "{}" not found'.format(backend))
