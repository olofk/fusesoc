from importlib import import_module
from os.path import dirname
from pkgutil import walk_packages

def get_edatool(name):
    return getattr(import_module('{}.{}'.format(__name__, name)),
                   name.capitalize())

def get_edatools():
    return [get_edatool(pkg) for _, pkg, _ in walk_packages([dirname(__file__)])]
