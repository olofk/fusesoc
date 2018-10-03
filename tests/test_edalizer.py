def test_generators():
    import os
    import tempfile

    from fusesoc.edalizer import Edalizer
    from fusesoc.core import Core

    tests_dir = os.path.dirname(__file__)
    cores_dir = os.path.join(tests_dir, "capi2_cores", "misc")

    core1 = Core(os.path.join(cores_dir, 'generators.core'))
    core2 = Core(os.path.join(cores_dir, 'generate.core'))

    build_root = tempfile.mkdtemp(prefix='export_')
    cache_root = tempfile.mkdtemp(prefix='export_cache_')
    export_root = os.path.join(build_root, 'exported_files')
    eda_api = Edalizer(core2.name,
                       {'tool' : 'icarus'},
                       [core1, core2],
                       cache_root=cache_root,
                       work_root=os.path.join(build_root, 'work'),
                       export_root=export_root).edalize
    gendir = os.path.join(cache_root,
                          "generated",
                          "generate-testgenerate_without_params_0")
    assert os.path.isfile(os.path.join(gendir, "generated.core"))
    assert os.path.isfile(os.path.join(gendir, "testgenerate_without_params_input.yml"))
    gendir = os.path.join(cache_root,
                          "generated",
                          "generate-testgenerate_with_params_0")
    assert os.path.isfile(os.path.join(gendir, "generated.core"))
    assert os.path.isfile(os.path.join(gendir, "testgenerate_with_params_input.yml"))
