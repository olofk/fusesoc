import argparse
import os

class FileAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, [os.path.abspath(values[0])])

class Plusargs:
    def __init__(self, items):
        self.items = items

    def add_arguments(self, parser):
        for item in self.items:
            tmp = self.items.get(item).split(' ',1)
            _name = '--' + str(item)

            if len(tmp) > 1:
                _help = tmp[1]
            else:
                _help = None
            _type = tmp[0].strip()
            if _type == 'int':
                parser.add_argument(_name, type=int, nargs=1, help=_help)
            elif _type == 'str':
                parser.add_argument(_name, type=str, nargs=1, help=_help)
            elif _type == 'bool':
                parser.add_argument(_name, action='store_true', help=_help)
            elif _type == 'file':
                parser.add_argument(_name, type=str, nargs=1, action=FileAction)
            else:
                raise Exception("Unknown plusargs type '"+_type+"'")
