import os
import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

class FusesocConfigParser(configparser.SafeConfigParser):
    def __init__(self, config_file):
        if sys.version[0] == '2':
            configparser.SafeConfigParser.__init__(self)
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
                print("Unknown version: \"" + id_string[1].strip()+'" in ' + config_file)
        except IndexError:
            raise SyntaxError("Could not find API version in " + config_file)
        try:
            self.readfp(f)
        except configparser.MissingSectionHeaderError:
            raise SyntaxError("Missing section header")
        except configparser.ParsingError as e:
            raise SyntaxError(e.message)
        except configparser.DuplicateSectionError as e:
            raise SyntaxError(e.message)

    def get_section(self, section):
        if self.has_section(section):
            return dict(self.items(section))
        else:
            return {}
