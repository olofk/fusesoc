import os
import shutil
import pytest

from test_common import compare_file, get_core, get_sim, sim_params

tests_dir = os.path.dirname(__file__)
core      = get_core("mor1kx-generic")
backend   = get_sim('rivierapro', core)
#backend.toplevel = backend.system.simulator['toplevel']
ref_dir   = os.path.join(tests_dir, __name__)
work_root = backend.work_root

def test_rivierapro_configure():

    backend.configure(sim_params)

    for f in ['fusesoc_build_rtl.tcl',
              'fusesoc_build_vpi.tcl',
              'fusesoc_launch.tcl',
              'fusesoc_main.tcl',
              'fusesoc_run.tcl']:
        with open(os.path.join(ref_dir, f)) as fref, open(os.path.join(work_root, f)) as fgen:
            assert fref.read() == fgen.read(), f
