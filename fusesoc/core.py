from fusesoc.capi1.core import Core as Capi1Core
from fusesoc.capi2.core import Core as Capi2Core

class Core(object):
    
    def __new__(cls, *args, **kwargs):
        with open(args[0]) as f:
            first_line = f.readline().split()[0]
            if  first_line == 'CAPI=1':
                return Capi1Core(*args, **kwargs)
            elif first_line == 'CAPI=2:':
                return Capi2Core(*args, **kwargs)
            else:
                raise RuntimeError("Unknown file type")
