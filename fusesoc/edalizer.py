import logging
import os
import shutil
import yaml

from fusesoc.vlnv import Vlnv

logger = logging.getLogger(__name__)

class Edalizer(object):

    def __init__(self, vlnv, flags, cores, cache_root, work_root, export_root=None):
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
        generators   = {}
        parameters   = {}
        scripts      = {}
        tool_options = {}
        vpi          = []

        _flags = flags.copy()
        core_queue = cores[:]
        core_queue.reverse()
        while core_queue:
            core = core_queue.pop()
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

            #Extract generators if defined in CAPI
            if hasattr(core, 'get_generators'):
                generators.update(core.get_generators(_flags))

            #Run generators
            if hasattr(core, 'get_ttptttg'):
                for _instance, _generator, _params in core.get_ttptttg(_flags):
                    if not _generator in generators:
                        raise RuntimeError("Could not find generator '{}' requested by {}".format(_generator, core.name))
                    core_queue += generate(
                        generators[_generator],
                        _instance,
                        _params,
                        cache_root,
                        core.files_root,
                        core.name)

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

#Edalizer decides on working directory and scans for core files afterwards
def generate(generator, name, parameters, cache_root, files_root, core_name):
    """Run a parametrized generator

    Args:
        generator (dict): The generator to run
        name (str): Name of the parametrized generator instance
        parameters (dict): Instance parameters to use for the generator
        cache_root (str): The directory where to store the generated cores
        files_root (str): Root directory of the core calling the generator
        core_name (Vlnv): VLNV of the core calling the generator

    Returns:
        list: Cores created by the generator
"""

    from fusesoc.core import Core
    from fusesoc.utils import Launcher

    vlnv_str = ':'.join([core_name.vendor,
                         core_name.library,
                         core_name.name+'-'+name,
                         core_name.version])
    vlnv = Vlnv(vlnv_str)

    generator_cwd = os.path.join(cache_root, 'generated', vlnv.sanitized_name)
    generator_input_file  = os.path.join(generator_cwd, name+'_input.yml')
    generator_input = {
        'files_root' : os.path.abspath(files_root),
        'gapi'       : '1.0',
        'parameters' : parameters,
        'vlnv'       : vlnv_str,
    }

    logger.info('Generating ' + str(vlnv))
    if not os.path.exists(generator_cwd):
        os.makedirs(generator_cwd)
    with open(generator_input_file, 'w') as f:
        f.write(yaml.dump(generator_input))

    args = [os.path.join(os.path.abspath(generator.root), generator.command),
            generator_input_file]

    if generator.interpreter:
        args[0:0] = [generator.interpreter]

    Launcher(args[0], args[1:],
             cwd=generator_cwd).run()

    cores = []
    logger.debug("Looking for genererated cores in " + generator_cwd)
    for root, dirs, files in os.walk(generator_cwd):
        for f in files:
            if f.endswith('.core'):
                try:
                    cores.append(Core(os.path.join(root, f)))
                except SyntaxError as e:
                    w = "Failed to parse generated core file " + f + ": " + e.msg
                    raise RuntimeError(w)
    logger.debug("Found " + ', '.join(str(c.name) for c in cores))
    return cores
