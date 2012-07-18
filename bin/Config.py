#import ConfigParser as configparser
import configparser
import os
#FIXME: Turn into singleton
DEFAULT_VALUES = {'prefix'       : os.getcwd(),
                  'build_root'   : '%(prefix)s/build',
                  'cache_root'   : '%(prefix)s/cache',
                  'cores_root'   : '%(prefix)s/cores',
                  'systems_root' : '%(prefix)s/systems'}
class Config:
    def __init__(self, config_file):
        print 
        config = configparser.SafeConfigParser(DEFAULT_VALUES)
        config.readfp(open(config_file))

        self.build_root = config.get('main','build_root')
        self.cache_root = config.get('main','cache_root')
        self.cores_root = config.get('main','cores_root')
        self.systems_root = config.get('main','systems_root')

    def get_systems(self):
        systems = {}
        for d in os.listdir(self.systems_root):
            f = os.path.join(self.systems_root, d, d+'.system')
            if os.path.exists(f):
                systems[d] = f
        return systems

    def get_cores(self):
        cores = {}
        for d in os.listdir(self.cores_root):
            f = os.path.join(self.cores_root, d, d+'.core')
            if os.path.exists(f):
                cores[d] = f
        return cores
        
