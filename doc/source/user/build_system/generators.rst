.. _ug_build_system_generators:

Generators: produce and specialize cores on demand
==================================================

Generators are a powerful way to generate parts of a hardware design on the fly.
Under the hood, generators are user-provided helper tools which are called by FuseSoC during the build process.

When to use generators
----------------------

FuseSoC :term:`core files` list files which are natively used by the backends, such as VHDL/(System)Verilog files, constraints, TCL scripts, hex files for ``$readmemh()``, etc.
There are however many cases where these files need to be created from another format.
Examples of this are Chisel/MyHDL/Migen source code which output Verilog, C programs that are compiled into a format suitable to be preloaded into memories, or any kind of description formats used to create HDL files.

The three parts of a generator
------------------------------

The generators support consists of three parts:

#. Provide the generator itself, which is a user-provided program.
   It is called by FuseSoC during the build process.
#. Register the generator in a ``generator`` section in a :term:`core file`, describing the generator and how to call it.
#. Finally, use a ``generate`` section to invoke the generator.
   The ``generate`` section is used similar to a ``fileset`` section.

Read on for a step-by-step explanation how generators can be used in FuseSoC.

An example: the multiblinky core
--------------------------------

To illustrate the declaration and use of generators the following sections refer to a complete example called ``multiblinky``, which extends the :ref:`blinky example <ug_build_system_core_files_example_blinky>` shown previously.
MultiBlinky uses a generator to generate a SystemVerilog file on the fly which instantiates ``blinky`` a configurable number of times.

The complete code is available in the `FuseSoC source tree <https://github.com/olofk/fusesoc>`_ in the ``tests/userguide/multiblinky`` directory.
The following files are part of the example.

.. code-block:: console

   $ tree tests/userguide/multiblinky/
   tests/userguide/multiblinky/
   ├── multiblinky.core
   ├── tb
   │   └── multiblinky_tb.sv
   └── util
      ├── blinky-generator.core
      └── blinky-generator.py

Files in ``util`` are related to the generator itself.
The generator is then called (used) in ``multiblinky.core``.

Creating a generator
--------------------

A generator is a callable command-line application (often a script), written in any programming language.

Below is an example of a generator to create a SystemVerilog module ``multiblinky`` within a file ``multiblinky.sv``, which instantiates the module ``blinky`` a parametrizable number of times.

.. literalinclude:: ../../../../tests/userguide/multiblinky/util/blinky-generator.py
   :language: python3
   :caption: ``blinky-generator.py``, an exemplary FuseSoC generator
   :name: ug_build_system_generators_blinky_generator_py
   :lines: 4-

.. note::

   FuseSoC provides the helper class :class:`fusesoc.capi2.Generator` to simplify code below significantly.
   However, to ease the writing of generators in other programming languages we show a pure Python implementation.

Input to the generator: the GAPI file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The generator is called by FuseSoC with a single command-line argument: the path to a configuration file in :term:`GAPI` format.
Here is a commented example of a GAPI file passed to a generator.

.. code-block:: yaml

  # An exemplary GAPI file, input to blinky-generator.py.

  # GAPI version, always 1.0 (currently).
  gapi: '1.0'
  # Proposed name of the generated core
  vlnv: fusesoc:examples:multiblinky-my_blinkygenerator:1.0.0
  # Source file path
  files_root: /some/path/multiblinky
  # Parameters passed to the generator
  parameters:
    blinky_count: 3

Refer to :ref:`ref_gapi` for the complete format description.

Expected output from the generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

XXX: TODO

Registering a generator
-----------------------

To register a generator, write a :term:`core file` with a ``generate`` section.
It is recommended to place this section in a separate core file, as shown below.

.. literalinclude:: ../../../../tests/userguide/multiblinky/util/blinky-generator.core
   :language: yaml
   :caption: ``blinky-generator.core``, a core file to register the ``blinky-generator.py`` generator.
   :name: ug_build_system_generators_blinky_generator_core

In this example the generator is called ``blinky-generator``; this name is used later when referring to the generator.

The ``generator.NAME`` section support the following arguments:

* ``description`` (optional): A description of the generator.
* ``command``: The command to run.
* ``interpreter`` (optional): When the generator is called the ``command`` is prefixed with the ``interpreter``, e.g. ``python3``, or ``perl``.

Refer to the :ref:`CAPI2 reference documentation <ref_capi2>` for more details.

When FuseSoC calls the generator it invokes ``<interpreter> <command> <gapi-file-path>`` (``interpreter`` is left out if not defined).

To check the generator is successfully registered call ``fusesoc gen list``.

.. code-block:: console

   $ fusesoc gen list

   Available generators:

   Core                                      Generator
   ===================================================
   fusesoc:examples:blinky-generator:1.0.0 : blinky-generator : Generate multiblinky, a file with multiple blinky instances


Invoking a generator
--------------------

The final piece of the generators machinery is to parametrize and invoke the generator.
The example below shows the ``multiblinky.core`` file, which makes use of the ``blinky-generator`` generator.

.. literalinclude:: ../../../../tests/userguide/multiblinky/multiblinky.core
   :language: yaml
   :caption: ``multiblinky.core``
   :name: ug_build_system_generators_multiblinky_core
   :end-at: toplevel: multiblinky

Three steps are necessary to invoke a generator:

#. Depend on the generator :term:`core` (the core file containing the ``generator`` section).
#. Add a ``generate`` section to define a named parametrized **generator instance**.
#. Add the generator instance to the desired target(s).

The ``generate`` section has a sub-section for each named generator instance.
The following attributes are available in each ``generate.NAME`` section.

* ``generator``: Name of the generator (matching the ``generator.NAME.name`` attribute).
* ``parameters``: A :term:`YAML` data structure with parameters.
  This structure is passed on without modification to the generator, allowing the passing of arbitrary data types, including nested structures.

How FuseSoC calls generators
----------------------------

When FuseSoC is launched and a core target using a generator is processed, the following will happen for each entry in the target's `generate` entry.

1. A key lookup is performed in the core file's `generate` section to find the generator configuration.
2. FuseSoC checks that it has registered a generator by the name specified in the `generator` entry of the configuration.
3. FuseSoC calculates a unique VLNV for the generator instance by taking the calling core's VLNV and concatinating the name field with the generator instance name.
4. A directory is created under <cache_root>/generated with a sanitized version of the calculated VLNV. This directory is where the output from the generator eventually will appear.
5. A yaml configuration file is created in the generator output directory. The parameters from the instance are passed on to this file. FuseSoC will set the files root of the calling core as `files_root` and add the calculated vlnv.
6. FuseSoC will switch working directory to the generator output directory and call the generator, using the command found in the generator's `command` field and with the created yaml file as command-line argument.
7. When *all* generators have successfully completed, FuseSoC will scan the generator output directories of the generators for new core files, and insert them into the list of available cores. This updated list of cores is then resolved to include dependencies.
