import sys
import yaml

class Generator(object):
    filesets   = {}
    parameters = {}
    targets    = {}
    def __init__(self):
        with open(sys.argv[1]) as f:
            data = yaml.load(f)

            self.config     = data.get('parameters')
            self.files_root = data.get('files_root')
            self.vlnv       = data.get('vlnv')

            #Edalize decide core_file dir. generator creates file
            self.core_file = self.vlnv.split(':')[2]+'.core'

    def add_files(self, files, fileset='rtl', targets=['default']):
        if not fileset in self.filesets:
            self.filesets[fileset] = {'files' : []}
        self.filesets[fileset]['files'] = files

        for target in targets:
            if not target in self.targets:
                self.targets[target] = {'filesets' : []}
            if not fileset in self.targets[target]['filesets']:
                self.targets[target]['filesets'].append(fileset)

    def add_parameter(self, parameter, data={}, targets=['default']):
        self.parameters[parameter] = data

        for target in targets:
            if not target in self.targets:
                self.targets[target] = {}
            if not 'parameters' in self.targets[target]:
                self.targets[target]['parameters'] = []
            if not parameter in self.targets[target]['parameters']:
                self.targets[target]['parameters'].append(parameter)
            
    def write(self):
        with open(self.core_file,'w') as f:
            f.write('CAPI=2:\n')
            coredata = {
                'name'       : self.vlnv,
                'filesets'   : self.filesets,
                'parameters' : self.parameters,
                'targets'    : self.targets,
            }
            f.write(yaml.dump(coredata))
