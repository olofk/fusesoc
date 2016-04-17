from fusesoc.build.quartus import Quartus
from fusesoc.build.ise import Ise
from fusesoc.build.vivado import Vivado

def BackendFactory(system):
    if system.backend_name == 'quartus':
        return Quartus(system)
    elif system.backend_name == 'ise':
        return Ise(system)
    elif system.backend_name == 'vivado':
        return Vivado(system)
    else:
        raise RuntimeError('Backend "{}" not found'.format(system.backend_name))
