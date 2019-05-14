import os
import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
    from ConfigParser import SafeConfigParser as CP
else:
    import configparser
    from configparser import ConfigParser as CP

class FusesocConfigParser(CP):
    def __init__(self, config_file):
        if sys.version[0] == '2':
            CP.__init__(self)
        else:
            super(FusesocConfigParser, self).__init__()
        if not os.path.exists(config_file):
            raise Exception("Could not find " + config_file)
        f = open(config_file)
        id_string = f.readline().split('=')

        if id_string[0].strip().upper() in ['CAPI', 'SAPI']:
            self.type = id_string[0]
        else:
            raise SyntaxError("Could not find API type in " + config_file)
        try:
            self.version = int(id_string[1].strip())
        except ValueError:
                raise SyntaxError("Unknown version '{}'".format(id_string[1].strip()))

        except IndexError:
            raise SyntaxError("Could not find API version in " + config_file)
        if sys.version[0] == '2':
            exceptions = (configparser.ParsingError,
                          configparser.DuplicateSectionError)
        else:
            exceptions = (configparser.ParsingError,
                          configparser.DuplicateSectionError,
                          configparser.DuplicateOptionError)
        try:
            if sys.version[0] == '2':
                self.readfp(f)
            else:
                self.read_file(f)
        except configparser.MissingSectionHeaderError:
            raise SyntaxError("Missing section header")
        except exceptions as e:
            raise SyntaxError(e.message)

    def get_section(self, section):
        if self.has_section(section):
            return dict(self.items(section))
        else:
            return {}
