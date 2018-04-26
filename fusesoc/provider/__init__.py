from importlib import import_module

def get_provider(name):
    return getattr(import_module('{}.{}'.format(__name__, name)),
                   name.capitalize())
