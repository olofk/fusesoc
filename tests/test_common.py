import os

tests_dir = os.path.dirname(__file__)
build_root = os.path.join(tests_dir, 'build')
cache_root = os.path.join(tests_dir, 'cache')
cores_root = os.path.join(tests_dir, 'cores')
library_root = os.path.join(tests_dir, 'libraries')

from fusesoc.config import Config
from fusesoc.coremanager import CoreManager

config = Config()
config.build_root = build_root
config.cache_root = cache_root
common_cm = CoreManager(config)
common_cm.add_cores_root(cores_root)
