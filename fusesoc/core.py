import logging

from fusesoc.capi1.core import Core as Capi1Core
from fusesoc.capi2.core import Core as Capi2Core


logger = logging.getLogger(__name__)


class Core(object):
    
    def __new__(cls, *args, **kwargs):
        with open(args[0]) as f:
            l = f.readline().split()
            if l:
                first_line = l[0]
            else:
                first_line = ''
            if  first_line == 'CAPI=1':
                return Capi1Core(*args, **kwargs)
            elif first_line == 'CAPI=2:':
                return Capi2Core(*args, **kwargs)
            else:
                error_msg = 'The first line of the core file {} must be "CAPI=1" or "CAPI=2:".'.format(args[0])
                error_msg += '  The first line of this core file is "{}".'.format(first_line)
                if first_line == 'CAPI=2':
                    error_msg += '  Just add a colon on the end!'
                logger.warning(error_msg)
                raise RuntimeError("Unknown file type")
