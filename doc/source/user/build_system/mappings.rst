.. _ug_build_system_mappings:

Mappings: Replace cores in the dependency tree
==============================================

Mappings allow a user of a core to substitute dependencies of the core with other cores without having to edit any of the core or it's dependencies files.
An example use case is making use of an existing core but substituting one of it's dependencies with a version that some desired changes (e.g. bug fixes).

If you are looking to provide a core with multiple implementations, virtual cores is the recommended and more semantic solution.
See :ref:`ug_build_system_virtual_cores` for more information on virtual cores.
Note: virtual cores can also be substituted in mappings.

Declaring mappings
------------------

Each core file can have one mapping.
An example mapping core file:

.. code:: yaml

    name: "local:map:override_fpu_and_fifo"
    mapping:
      "vendor:lib:fpu":  "local:lib:fpu"
      "vendor:lib:fifo": "local:lib:fifo"

The example above is a core file with only a mapping property, but any core file may contain a mapping in addition to other properties (e.g. filesets, targets & generators).

Applying mappings
-----------------

To apply a mapping, provide the VLNV of the core file that contains the desired
mapping with `fusesoc run`'s `--mapping` argument. Multiple mappings may be
provided as shown below.

.. code:: sh

    fusesoc run \
      --mapping local:map:override_fpu_and_fifo \
      --mapping local:map:another_mapping \
      vendor:top:main
