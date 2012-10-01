import sys
if sys.version[0] == '2':
    import ConfigParser as configparser
else:
    import configparser

from orpsoc.config import Config
from orpsoc.provider import ProviderFactory
import os
import shutil
import subprocess

DEFAULT_VALUES = {'include_files' : '',
                  'provider'      : '',
                  'rtl_files'     : '',
                  'tb_files'      : ''}
class Core:
    def __init__(self, core_file=None, name=None, core_root=None):
        if core_file:
            config = configparser.SafeConfigParser(DEFAULT_VALUES)
            #FIXME: Check if file exists
            config.readfp(open(core_file))

            self.name = config.get('main','name')

            self.core_root = os.path.dirname(core_file)

            provider_name = config.get('main', 'provider')
            if provider_name:
                self.cache_dir = os.path.join(Config().cache_root, self.name)
                self.files_root = self.cache_dir
                items    = config.items(provider_name)
                self.provider = ProviderFactory(provider_name, items)
            else:
                self.provider = None
                self.files_root = self.core_root

            self.rtl_files     = config.get('main', 'rtl_files').split()
            self.include_files = config.get('main', 'include_files').split()
            self.include_dirs  = list(set(map(os.path.dirname,self.include_files)))
            self.tb_files      = config.get('main', 'tb_files').split()

        else:
            self.name = name

            self.core_root = core_root
            self.cache_root = core_root
            self.files_root = core_root

            self.provider = None

            self.rtl_files = []
            self.include_files = []
            self.include_dirs = []
            self.tb_files = []

        
    def cache_status(self):
        if self.provider:
            return self.provider.status(self.cache_dir)
        else:
            return 'local'

    def setup(self):
        if self.provider:
            self.provider.fetch(self.cache_dir)

    def export(self, dst_dir):
            
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        src_dir = self.files_root

        #FIXME: Separate tb_files to an own directory tree (src/tb/core_name ?)
        src_files = self.rtl_files + self.include_files + self.tb_files

        dirs = list(set(map(os.path.dirname,src_files)))
        for d in dirs:
            os.makedirs(os.path.join(dst_dir, d))

        for f in src_files:
            shutil.copyfile(os.path.join(src_dir, f), 
                            os.path.join(dst_dir, f))
        
    def patch(self, dst_dir):
        #FIXME: Use native python patch instead
        patch_root = os.path.join(Config().cores_root, self.name, 'patches')
        if os.path.exists(patch_root):
            for f in sorted(os.listdir(patch_root)):
                try:
                    subprocess.call(['patch','-p1', '-s',
                                     '-d', os.path.join(dst_dir),
                                     '-i', os.path.join(patch_root, f)])
                except OSError:
                    print("Error: Failed to call external command 'patch'")
                    return False
        return True
