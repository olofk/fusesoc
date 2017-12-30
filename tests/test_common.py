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

def compare_file(ref_dir, work_root, name):
    import difflib
    reference_file = os.path.join(ref_dir, name)
    generated_file = os.path.join(work_root, name)

    assert os.path.exists(generated_file)

    with open(reference_file) as f1, open(generated_file) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        return diff

def compare_files(ref_dir, work_root, files):
    import difflib

    for f in files:
        reference_file = os.path.join(ref_dir, f)
        generated_file = os.path.join(work_root, f)

        assert os.path.exists(generated_file)

        with open(reference_file) as fref, open(generated_file) as fgen:
            assert fref.read() == fgen.read(), f

def get_core(core):
    from fusesoc.main import _get_core
    
    return _get_core(common_cm, core)

def get_sim(sim, core, export=False):
    flags = {'target' : 'sim',
             'tool' : sim}
    return get_backend(core, flags, export)

def get_synth(tool, core, export=False):
    flags = {'target' : 'synth',
             'tool' : tool}
    return get_backend(core, flags, export)

def get_backend(core, flags, export):
    import os.path
    import tempfile
    import yaml
    from fusesoc.main import _import

    if export:
        export_root = os.path.join(build_root, core.name.sanitized_name, 'src')
    else:
        export_root = None
    work_root   = os.path.join(build_root,
                               core.name.sanitized_name,
                               core.get_work_root(flags))
    eda_api = common_cm.setup(core.name, flags, work_root, export_root)

    (h, eda_api_file) = tempfile.mkstemp()
    with open(eda_api_file,'w') as f:
        f.write(yaml.dump(eda_api))

    return _import(flags['tool'])(eda_api_file=eda_api_file, work_root=work_root)

cmdlineargs = ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'.split()
plusargs    = ' --plusarg_bool --plusarg_int=42 --plusarg_str=hello'.split()
vlogdefines = ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'.split()
vlogparams  = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'.split()

sim_params = vlogparams + vlogdefines + plusargs
