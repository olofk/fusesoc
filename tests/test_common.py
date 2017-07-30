def compare_file(ref_dir, work_root, name):
    import difflib
    import os
    reference_file = os.path.join(ref_dir, name)
    generated_file = os.path.join(work_root, name)

    assert os.path.exists(generated_file)

    with open(reference_file) as f1, open(generated_file) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        return diff

def compare_files(ref_dir, work_root, files):
    import difflib
    import os

    for f in files:
        reference_file = os.path.join(ref_dir, f)
        generated_file = os.path.join(work_root, f)

        assert os.path.exists(generated_file)

        with open(reference_file) as fref, open(generated_file) as fgen:
            assert fref.read() == fgen.read(), f

def get_core(core):
    import os
    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.main import _get_core

    tests_dir = os.path.dirname(__file__)

    Config().build_root = os.path.join(tests_dir, 'build')
    Config().cache_root = os.path.join(tests_dir, 'cache')
    cores_root = os.path.join(tests_dir, 'cores')

    CoreManager().add_cores_root(cores_root)
    return _get_core(core)

def get_sim(sim, core, export=False):
    import os.path
    from fusesoc.coremanager import CoreManager
    from fusesoc.config import Config
    from fusesoc.main import _import

    flags = {'flow' : 'sim',
             'tool' : sim}

    eda_api = CoreManager().get_eda_api(core.name, flags)
    export_root = os.path.join(Config().build_root, core.name.sanitized_name, 'src')
    work_root   = os.path.join(Config().build_root, core.name.sanitized_name, 'sim-'+sim)
    
    CoreManager().setup(core.name, flags, export=export, export_root=export_root)
    return _import('simulator', sim)(eda_api=eda_api, work_root=work_root)

def get_synth(tool, core, export=False):
    import os.path
    from fusesoc.config import Config
    from fusesoc.coremanager import CoreManager
    from fusesoc.main import _import

    flags = {'flow' : 'synth',
             'tool' : tool}

    eda_api = CoreManager().get_eda_api(core.name, flags)
    work_root   = os.path.join(Config().build_root, core.name.sanitized_name, 'bld-'+tool)
    return _import('build', core.main.backend)(eda_api=eda_api, work_root=work_root)

cmdlineargs = ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'.split()
plusargs    = ' --plusarg_bool --plusarg_int=42 --plusarg_str=hello'.split()
vlogdefines = ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'.split()
vlogparams  = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'.split()

sim_params = vlogparams + vlogdefines + plusargs
