import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.config import Config
from orpsoc.provider import ProviderFactory
import os

DEFAULT_VALUES = {'include_dirs'  : '',
                  'include_files' : '',
                  'provider'      : '',
                  'tb_files'      : ''}
class Core:
    def __init__(self, core_file=None):
        self.rtl_files = []
        self.include_files = []
        self.tb_files = []
        provider_name = ''
        if core_file:

            config = configparser.SafeConfigParser(DEFAULT_VALUES)
            config.readfp(open(core_file))
            self.name = config.get('main','name')

            self.rtl_files = self._get_files(config, 'rtl_files')
            self.include_files = self._get_files(config, 'include_files')
            self.include_dirs = self._get_files(config, 'include_dirs')
            self.tb_files = self._get_files(config, 'tb_files')
            provider_name = config.get('main', 'provider')

        if provider_name:
            self.cache_dir = os.path.join(Config().cache_root, self.name)
            self.files_root = self.cache_dir
            items    = config.items(provider_name)
            self.provider = ProviderFactory(provider_name, items)
        else:
            self.provider = None
            if core_file:
                self.files_root = os.path.dirname(core_file)

    def cache_status(self):
        if self.provider:
            return self.provider.status(self.cache_dir)
        else:
            return 'local'

    def setup(self):
        if self.provider:
            self.provider.fetch(self.cache_dir)

    def patch(self):
        print("FIXME: Need to check for python patch bindings. Do we need a file list or at least base dir for core too?")

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
        return self.files_root

    def set_root(self, root):
        self.files_root = root

    def _get_files(self, config, identifier):
        files = config.get('main', identifier).split('\n')
        if '' in files:
            files.remove('')
        return files
