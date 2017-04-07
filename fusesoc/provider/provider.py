import os

class Provider(object):
    def __init__(self, config, core_root, files_root):
        self.config = config
        self.core_root = core_root
        self.files_root = files_root

        self.cachable = True
        if 'cachable' in config:
            self.cachable = not (config.get('cachable') == 'false')

    def clean_cache(self):
        if os.path.exists(self.files_root):
            shutil.rmtree(self.files_root)

    def fetch(self):
        status = self.status()
        if status == 'empty':
            self._checkout(self.files_root)
            return True
        elif status == 'outofdate':
            self.clean_cache()
            self._checkout(self.files_root)
            return True
        elif status == 'downloaded':
            return False
        raise RuntimeError("Provider status is: '" + status + "'. This shouldn't happen")

    def status(self):
        if not self.cachable:
            return 'outofdate'
        if not os.path.isdir(self.files_root):
            return 'empty'
        else:
            return 'downloaded'
