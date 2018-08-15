import pytest

def test_icestorm():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_icestorm_0'
    tool         = 'icestorm'
    tool_options = {
        'yosys_synth_options' : ['some', 'yosys_synth_options'],
        'arachne_pnr_options' : ['a', 'few', 'arachne_pnr_options'],
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.ys'])

    f = os.path.join(work_root, 'pcf_file.pcf')
    with open(f, 'a'):
        os.utime(f, None)

    backend.build()
    compare_files(ref_dir, work_root, ['yosys.cmd'])
    compare_files(ref_dir, work_root, ['arachne-pnr.cmd'])
    compare_files(ref_dir, work_root, ['icepack.cmd'])

def test_icestorm_minimal():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend_minimal, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'minimal')
    name         = 'test_icestorm_0'
    tool         = 'icestorm'

    (backend, work_root) = setup_backend_minimal(name, tool, [{'name' : 'pcf_file.pcf', 'file_type' : 'PCF'}])
    backend.configure('')

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.ys'])

    f = os.path.join(work_root, 'pcf_file.pcf')
    with open(f, 'a'):
        os.utime(f, None)

    backend.build()
    compare_files(ref_dir, work_root, ['yosys.cmd'])
    compare_files(ref_dir, work_root, ['arachne-pnr.cmd'])
    compare_files(ref_dir, work_root, ['icepack.cmd'])

def test_icestorm_no_pcf():
    import os

    from edalize_common import compare_files, setup_backend_minimal, tests_dir

    name         = 'test_icestorm_0'
    tool         = 'icestorm'

    (backend, work_root) = setup_backend_minimal(name, tool, [])
    with pytest.raises(RuntimeError) as e:
        backend.configure('')
    assert "Icestorm backend requires a PCF file" in str(e.value)

def test_icestorm_multiple_pcf():
    import os

    from edalize_common import compare_files, setup_backend_minimal, tests_dir

    name         = 'test_icestorm_0'
    tool         = 'icestorm'

    (backend, work_root) = setup_backend_minimal(name, tool, [{'name' : 'pcf_file.pcf', 'file_type' : 'PCF'},
                                                              {'name' : 'pcf_file2.pcf', 'file_type' : 'PCF'}])
    with pytest.raises(RuntimeError) as e:
        backend.configure('')
    assert "Icestorm backend supports only one PCF file. Found pcf_file.pcf, pcf_file2.pcf" in str(e.value)

def test_icestorm_nextpnr():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__, 'nextpnr')
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_icestorm_0'
    tool         = 'icestorm'
    tool_options = {
        'yosys_synth_options' : ['some', 'yosys_synth_options'],
        'arachne_pnr_options' : ['a', 'few', 'arachne_pnr_options'],
        'nextpnr_options'     : ['multiple', 'nextpnr_options'],
        'pnr'                 : 'next',
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    backend.configure(args)

    compare_files(ref_dir, work_root, ['Makefile',
                                       name+'.ys'])

    f = os.path.join(work_root, 'pcf_file.pcf')
    with open(f, 'a'):
        os.utime(f, None)

    backend.build()
    compare_files(ref_dir, work_root, ['yosys.cmd'])
    compare_files(ref_dir, work_root, ['nextpnr-ice40.cmd'])
    compare_files(ref_dir, work_root, ['icepack.cmd'])

def test_icestorm_invalid_pnr():
    import os
    import shutil
    from edalize_common import compare_files, setup_backend, tests_dir

    ref_dir      = os.path.join(tests_dir, __name__)
    paramtypes   = ['vlogdefine', 'vlogparam']
    name         = 'test_icestorm_0'
    tool         = 'icestorm'
    tool_options = {
        'pnr'                 : 'invalid',
    }

    (backend, args, work_root) = setup_backend(paramtypes, name, tool, tool_options)
    with pytest.raises(RuntimeError) as e:
        backend.configure(args)
    assert "nvalid pnr option 'invalid'. Valid values are 'arachne' for Arachne-pnr or 'next' for nextpnr" in str(e.value)
