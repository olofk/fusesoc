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
        self.cores_root = None
        config_file = './orpsoc.conf'
        if os.path.exists(config_file):
            config = configparser.SafeConfigParser(DEFAULT_VALUES)
            config.readfp(open('./orpsoc.conf'))

            self.build_root = config.get('main','build_root')
            self.cache_root = config.get('main','cache_root')
            self.cores_root = config.get('main','cores_root')
            self.systems_root = config.get('main','systems_root')
        else:
            self.build_root   = 'build'
            self.cache_root   = 'cache'
            if os.path.exists('cores'):
                self.cores_root   = 'cores'
            self.systems_root = 'systems'
    def get_systems(self):
        systems = {}
        for d in os.listdir(self.systems_root):
            f = os.path.join(self.systems_root, d, d+'.system')
            if os.path.exists(f):
                systems[d] = f
        return systems

