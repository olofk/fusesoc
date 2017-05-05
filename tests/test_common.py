def compare_file(ref_dir, work_root, name):
    import difflib
    import os
    reference_file = os.path.join(ref_dir, name)
    generated_file = os.path.join(work_root, name)

    assert os.path.exists(generated_file)

    with open(reference_file) as f1, open(generated_file) as f2:
        diff = ''.join(difflib.unified_diff(f1.readlines(), f2.readlines()))
        return diff

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
    from fusesoc.coremanager import CoreManager
    from fusesoc.main import _import

    flags = {'flow' : 'sim',
             'tool' : sim}

    eda_api = CoreManager().get_eda_api(core.name, flags)
    return _import('simulator', sim)(core,
                                     export=export,
                                     eda_api=eda_api)

def get_synth(tool, core, export=False):
    from fusesoc.coremanager import CoreManager
    from fusesoc.main import _import

    flags = {'flow' : 'synth',
             'tool' : tool}

    eda_api = CoreManager().get_eda_api(core.name, flags)
    return _import('build', core.main.backend)(core,
                                               export=export,
                                               eda_api=eda_api)

cmdlineargs = ' --cmdlinearg_bool --cmdlinearg_int=42 --cmdlinearg_str=hello'.split()
plusargs    = ' --plusarg_bool --plusarg_int=42 --plusarg_str=hello'.split()
vlogdefines = ' --vlogdefine_bool --vlogdefine_int=42 --vlogdefine_str=hello'.split()
vlogparams  = '--vlogparam_bool --vlogparam_int=42 --vlogparam_str=hello'.split()

sim_params = vlogparams + vlogdefines + plusargs
