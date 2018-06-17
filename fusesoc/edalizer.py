import logging
import os
import shutil
import yaml
logger = logging.getLogger(__name__)

class Edalizer(object):

    def __init__(self, vlnv, flags, cores, work_root, export_root=None):
        if os.path.exists(work_root):
            for f in os.listdir(work_root):
                if os.path.isdir(os.path.join(work_root, f)):
                    shutil.rmtree(os.path.join(work_root, f))
                else:
                    os.remove(os.path.join(work_root, f))
        else:
            os.makedirs(work_root)

        logger.debug("Building EDA API")
        def merge_dict(d1, d2):
            for key, value in d2.items():
                if isinstance(value, dict):
                    d1[key] = merge_dict(d1.get(key, {}), value)
                elif isinstance(value, list):
                    d1[key] = d1.get(key, []) + value
                else:
                    d1[key] = value
            return d1

        files        = []
        parameters   = {}
        scripts      = {}
        tool_options = {}
        vpi          = []

        _flags = flags.copy()
        for core in cores:
            logger.info("Preparing " + str(core.name))
            core.setup()

            logger.debug("Collecting EDA API parameters from {}".format(str(core.name)))
            _flags['is_toplevel'] = (core.name == vlnv)

            #Extract files
            if export_root:
                files_root = os.path.join(export_root, core.sanitized_name)
                core.export(files_root, _flags)
            else:
                files_root = core.files_root

            rel_root = os.path.relpath(files_root, work_root)

            #Extract parameters
            merge_dict(parameters, core.get_parameters(_flags))

            #Extract tool options
            merge_dict(tool_options, core.get_tool_options(_flags))

            #Extract scripts
            merge_dict(scripts, core.get_scripts(rel_root, _flags))

            for file in core.get_files(_flags):
                if file.copyto:
                    _name = file.copyto
                    dst = os.path.join(work_root, _name)
                    _dstdir = os.path.dirname(dst)
                    if not os.path.exists(_dstdir):
                        os.makedirs(_dstdir)
                    shutil.copy2(os.path.join(files_root, file.name),
                                 dst)
                else:
                    _name = os.path.join(rel_root, file.name)
                files.append({
                    'name'            : _name,
                    'file_type'       : file.file_type,
                    'is_include_file' : file.is_include_file,
                    'logical_name'    : file.logical_name})
            #Extract VPI modules
            for _vpi in core.get_vpi(_flags):
                vpi.append({'name'         : _vpi['name'],
                            'src_files'    : [os.path.join(rel_root, f) for f in _vpi['src_files']],
                            'include_dirs' : [os.path.join(rel_root, i) for i in _vpi['include_dirs']],
                            'libs'         : _vpi['libs']})

        top_core = cores[-1]
        self.edalize = {
            'version'      : '0.2.0',
            'files'        : files,
            'hooks'        : scripts,
            'name'         : top_core.sanitized_name,
            'parameters'   : parameters,
            'tool_options' : {flags['tool'] : tool_options},
            'toplevel'     : top_core.get_toplevel(flags),
            'vpi'          : vpi,
        }

    def to_yaml(self, edalize_file):
        with open(edalize_file,'w') as f:
            f.write(yaml.dump(self.edalize))
        

