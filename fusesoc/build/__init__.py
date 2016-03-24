from fusesoc.build.quartus import Quartus
from fusesoc.build.ise import Ise

def BackendFactory(system):
    if system.backend_name == 'quartus':
        return Quartus(system)
    elif system.backend_name == 'ise':
        return Ise(system)
    else:
        raise RuntimeError('Backend "{}" not found'.format(system.backend_name))
