import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

import os

DEFAULT_VALUES = {'prefix'       : os.getcwd(),
                  'build_root'   : '%(prefix)s/build',
                  'cache_root'   : '%(prefix)s/cache',
                  'cores_root'   : '%(prefix)s/cores',
                  'systems_root' : '%(prefix)s/systems'}
class Config(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        #FIXME: Don't hardcode ./orpsoc.conf
        self.build_root = None
        self.cache_root = None
        self.cores_root = None
        self.systems_root = None
        config_file = './orpsoc.conf'
        if os.path.exists(config_file):
            config = configparser.SafeConfigParser(DEFAULT_VALUES)
            config.readfp(open('./orpsoc.conf'))

            self.build_root = config.get('main','build_root')
            self.cache_root = config.get('main','cache_root')
            self.cores_root = config.get('main','cores_root')
            self.systems_root = config.get('main','systems_root')

        if self.build_root is None:
            self.build_root   = 'build'
        if self.cache_root is None:
            self.cache_root   = 'cache'
        if self.cores_root is None and os.path.exists('cores'):
            self.cores_root   = 'cores'
        if self.systems_root is None and os.path.exists('systems'):
            self.systems_root = 'systems'
