import os

class VPI:
    def __init__(self, items):
        self.name          = items.get('name')
        self.src_files     = items.get('src_files').split()
        if items.get('include_files'):
            self.include_files = items.get('include_files').split()
        else:
            self.include_files = []

        self.include_dirs  = list(set(map(os.path.dirname, self.include_files)))

    def export(self):
        return self.src_files + self.include_files
