import logging
import os
from fusesoc.utils import Launcher
logger = logging.getLogger(__name__)

class Provider(object):
    def __init__(self, config, core_root, files_root):
        self.config = config
        self.core_root = core_root
        self.files_root = files_root

        self.cachable = not (config.get('cachable', '') == 'false')
        self.patches = config.get('patches', [])

    def clean_cache(self):
        if os.path.exists(self.files_root):
            shutil.rmtree(self.files_root)

    def fetch(self):
        status = self.status()
        if status == 'empty':
            self._checkout(self.files_root)
            _fetched = True
        elif status == 'outofdate':
            self.clean_cache()
            self._checkout(self.files_root)
            _fetched = True
        elif status == 'downloaded':
            _fetched = False
        else:
            raise RuntimeError("Provider status is: '" + status + "'. This shouldn't happen")
        if _fetched:
            self._patch()

    def _patch(self):
        for f in self.patches:
            patch_file = os.path.abspath(os.path.join(self.core_root, f))
            if os.path.isfile(patch_file):
                logger.debug("  applying patch file: " + patch_file + "\n" +
                             "                   to: " + os.path.join(self.files_root))
                try:
                    Launcher('git', ['apply', '--unsafe-paths',
                                     '--directory', self.files_root,
                                     patch_file]).run()
                except OSError:
                    raise RuntimeError("Failed to call 'git' for patching core")

    def status(self):
        if not self.cachable:
            return 'outofdate'
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'
