import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

import Config
import ProviderOpenCores
import ProviderLocal
import os

DEFAULT_VALUES = {'include_dirs'  : '',
                  'include_files' : '',
                  'tb_files'      : ''}
class Core:
    def __init__(self, core_file=None):
        self.rtl_files = []
        self.include_files = []
        self.tb_files = []
        if core_file:

            config = configparser.SafeConfigParser(DEFAULT_VALUES)
            config.readfp(open(core_file))
            self.name = config.get('main','name')

            self.rtl_files = self._get_files(config, 'rtl_files')
            self.include_files = self._get_files(config, 'include_files')
            self.include_dirs = self._get_files(config, 'include_dirs')
            self.tb_files = self._get_files(config, 'tb_files')

            provider = config.get('main', 'provider')
            items    = config.items(provider)
            self.provider = self.provider_factory(provider, items)

            config = Config.Config()

            if provider == 'local':
                self.root = os.path.dirname(core_file)
            else:
                self.root = os.path.join(config.cache_root, self.name)


    def setup(self):
        self.provider.fetch(self.root)

    def patch(self):
        print("FIXME: Need to check for python patch bindings. Do we need a file list or at least base dir for core too?")

    def provider_factory(self, provider, items):
        if provider == 'opencores':
            return ProviderOpenCores.ProviderOpenCores(dict(items))
        elif provider == 'local':
            return ProviderLocal.ProviderLocal()
        else:
            raise Exception('Unknown provider')

    def get_rtl_files(self):
        return self.rtl_files

    def set_rtl_files(self, rtl_files):
        self.rtl_files = rtl_files

    def get_include_dirs(self):
        return self.include_dirs

    def set_include_dirs(self, include_dirs):
        self.include_dirs = include_dirs

    def get_include_files(self):
        return self.include_files

    def set_include_files(self, include_files):
        self.include_files = include_files

    def get_tb_files(self):
        return self.tb_files

    def set_tb_files(self, tb_files):
        self.tb_files = tb_files

    def get_root(self):
        return self.root

    def set_root(self, root):
        self.root = root

    def _get_files(self, config, identifier):
        files = config.get('main', identifier).split('\n')
        if '' in files:
            files.remove('')
        return files
