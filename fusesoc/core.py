from fusesoc.capi1.core import Core as Capi1Core

class Core(object):
    
    def __new__(cls, *args, **kwargs):
        return Capi1Core(*args, **kwargs)
