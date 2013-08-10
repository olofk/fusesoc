import os
import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

class OrpsocConfigParser(configparser.SafeConfigParser):
    def __init__(self, config_file):
        if sys.version[0] == '2':
            configparser.SafeConfigParser.__init__(self)
        else:
            super(OrpsocConfigParser, self).__init__()
        if not os.path.exists(config_file):
            print("Could not find " + config_file)
            exit(1)
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
        self.readfp(f)

    def get_list(self, section, item):
        if self.has_option(section, item):
            return self.get(section, item).split()
        else:
            return []
        
