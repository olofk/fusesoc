class Provider(object):
    def __init__(self, config):
        pass

    def fetch(self):
        pass

    def status(self, local_dir):
        pass

from orpsoc.provider.opencores import ProviderOpenCores

def ProviderFactory(provider, items):
    if provider == 'opencores':
        return ProviderOpenCores(dict(items))
    else:
        raise Exception('Unknown provider')
