.. _ug_build_system_core_files:

Writing core files
==================

A :term:`core` is described in a core description file, or core file.

Core files are written in :term:`YAML` syntax and follow the FuseSoC's own CAPI (version 2) schema, which describes the structure of core files (e.g. which keys and values are allowed where).
Don't worry: using FuseSoC neither requires a full understanding of YAML, nor an up-front knowledge of CAPI.
However, some key facts about YAML are important.

Things one should know about YAML
---------------------------------

* **Whitespace matters** (as in Python): indentation is used to group settings together to form a hierarchy.
  The exact amount of whitespace used for indentation does not matter; typically two or four spaces are used.

* Think of a YAML file as a **hierarchical, typed data structure**.
  There are lists, dictionaries (key/value pairs), integers, strings, etc.

* YAML syntax provides **multiple ways to describe the same structure**.
  It does not matter to FuseSoC which syntax variant is used.
  For example, a list of items can be written in the following two, semantically identical ways.

  .. code-block:: yaml

     [ item1, item2 ]

  is semantically identical to

  .. code-block:: yaml

     - item1
     - item2

  The same is true for dictionaries (key/value pairs).

  .. code-block:: yaml

     { key1: value1, key2: value2 }

  is semantically identical to

  .. code-block:: yaml

     key1: value1
     key2: value2

  In most cases, the longer (second) form is preferred, as it is easier to make changes while keeping the diff easy to read.

For a quick introduction into most of YAML's features have a look at `Learn YAML in Y minutes <https://learnxinyminutes.com/docs/yaml/>`_.
The full YAML 1.2 specification is available at `yaml.org <https://yaml.org/spec/1.2/spec.html>`_ (it's not an easy read, though).

.. _ug_build_system_core_files_example_blinky:

An example: the blinky core
---------------------------

The following sections explain how to add FuseSoC support to a hardware project.
The code is taken from an example design in the `FuseSoC source tree <https://github.com/olofk/fusesoc>`_ in the ``tests/userguide/blinky`` directory.

The design consists of two SystemVerilog files, a testbench, a Xilinx constraint file (with pin mappings for a Nexys Video FPGA board), and finally, the FuseSoC core file.

.. code-block:: console

   $ tree tests/userguide/blinky/
   tests/userguide/blinky/
   ├── blinky.core
   ├── data
   │   └── nexys_video.xdc
   ├── rtl
   │   ├── blinky.sv
   │   └── macros.svh
   └── tb
      └── blinky_tb.sv

   3 directories, 5 files

To get started, here's the full ``blinky.core`` file.
The following sections will refer back to this example to discuss it in detail.

.. literalinclude:: ../../../../tests/userguide/blinky/blinky.core
   :language: yaml
   :caption: ``blinky.core``, an exemplary core file
   :name: ug_build_system_cb_blinky_full
   :linenos:

Naming the core file
--------------------

The core file can have any name, but it must end in ``.core``.
It is recommended to choose a file name matching the core name, as discussed below.

The first line: ``CAPI=2``
--------------------------

A core file always starts with the line ``CAPI=2``.
No other content (including comments) is allowed before this line, as FuseSoC uses this line to differentiate between different versions of the CAPI schema.
Only CAPI version 2 is specified at the moment.

.. _ug_build_system_core_name:

The core name, version, and description
---------------------------------------

Each core has a name, given in the ``name`` key.
Core names can be freely chosen, but need to follow a common structure called *VLNV*.
:term:`VLNV` stands the four parts of a core name, which are separated by colon (``:``): Vendor, Library, Name, and Version.

Version numbers should be three numbers in the form major.minor.patch and follow :term:`semantic versioning` (SemVer).

Cores can also have a description, given in the ``description`` key.
A description is optional, but recommended.

.. literalinclude:: ../../../../tests/userguide/blinky/blinky.core
   :language: yaml
   :start-at: name:
   :end-at: description:

In this example, the vendor is ``fusesoc``, the library is ``examples``, and the name of the core is ``blinky``.
The version is set to ``1.0.0``.

Specifying source files
-----------------------

A core typically consists of one or multiple source files.
Source files are grouped into file sets under the ``filesets`` key.

FuseSoC does neither mandate a specific grouping, nor naming of file sets.
It is common to use one file set for RTL (design) files, and one for testbench files.

The following example shows a single file set, ``rtl``, with a set of common keys.

.. literalinclude:: ../../../../tests/userguide/blinky/blinky.core
   :language: yaml
   :start-at: filesets:
   :end-at: file_type

For each named file set, several keys are supported:

* ``files``: An ordered list of source files.
  The list of source files is ordered: the files will be passed to the tool in exactly the given order.
  This is important, for example, in SystemVerilog, where packages need to be compiled before they can be used by subsequent source files.
* ``file_type``: The default file type for all files in the ``files`` list.
* ``depend``: Dependencies on other cores.
  Dependencies are explained in depth at :ref:`ug_build_system_dependencies`.

Source files
~~~~~~~~~~~~

Source files are resolved relative to the location of the core file and must be stored in the same directory as the core file, or in a subdirectory of it.
Source file names cannot be absolute paths, or start with ``../``.

Optionally, source files can have attributes; the file ``macros.vh`` is an example of that.
When specifying attributes, end the file name with a colon (``:``), and specify attributes as key-value pairs below it.
(Alternatively, the equivalent short form syntax can be used, e.g. ``macros.vh: {is_include_file: true}``.)

The most common attributes are:

* ``is_include_file``: The file is an include file. In Verilog and C/C++, this means the file is not passed to the tool directly, but instead the file is included by another source file.
  FuseSoC ensures that the tool finds the include file, e.g. by passing an appropriate include path to the tool.
* ``file_type``: Override the default file type of the fileset for this particular file.

Refer to the :ref:`CAPI2 reference documentation <ref_capi2>` for more details.

File types
~~~~~~~~~~

A file type describes the type of source file.
FuseSoC does not use this information itself, but passes it on to tool backends which then configure the tool appropriately depending on the file type encountered.

Commonly used file types are:

* ``verilogSource``: Verilog source code, up to Verilog-2001.
  Files ending in ``.v`` or ``.vh`` should use this type.
* ``systemVerilogSource``: SystemVerilog source code (design and test code).
  Files ending in ``.sv`` or ``.svh`` should use this type.
* ``vhdlSource``: VHDL source code.
  Files ending in ``.vhd`` or ``.vhdl`` should use this file type.

Refer to the :ref:`CAPI2 reference documentation <ref_capi2>` for more details.

Targets
-------

A :term:`target` can be seen as something you would like to do with the source code in the core: synthesize it, simulate it, lint it.
Targets are specified as dictionaries under the ``targets`` top-level key.

.. literalinclude:: ../../../../tests/userguide/blinky/blinky.core
   :language: yaml
   :start-at: targets:
   :end-at:        - clk_freq_hz=100000000
   :name: ug_build_system_cb_targets

The blinky example shown above defines three targets: the ``default`` target, a ``sim`` target to simulate the design, and a ``synth`` target to synthesize it.
Many designs also define a ``lint`` target to run static analysis jobs.
The ``sim`` and ``synth`` targets are optional and could have had any name.
The ``default`` target is special and required.

Within a target
~~~~~~~~~~~~~~~

Within each target block multiple keys determine what the target does.
The most common keys are:

* ``filesets``: An ordered list of file sets (source files) included in the target.
* ``description`` (optional): A description of the target.
* ``toplevel`` (optional): The name of the design toplevel.
  (For advanced scenarios it is possible to specify a list of multiple toplevels instead of just a single one.)
* ``default_tool`` (optional): The default tool to be used to build the target.
  The tool can also be set or overridden through a FuseSoC command-line argument.
* ``tools`` (optional): Tool-specific settings, grouped by tool name.
* ``parameters`` (optional): Parameters (Verilog parameters and defines, VHDL generics, etc.) to be passed to the design, or forced to a certain value.

The ``filesets_append`` key is part of an inheritance schema and explained further in section :ref:`ug_build_system_targets_inheritance`.

The ``default`` target
~~~~~~~~~~~~~~~~~~~~~~

The ``default`` target is the only required target.
It serves two purposes:

* The ``default`` target is used if no other target is explicitly selected when running FuseSoC.
* The contents of the ``default`` target are used if the core is used as dependency (described in detail in :ref:`ug_build_system_dependencies`).

All reusable code in the core should go into the ``default`` target: RTL files, lint waivers, reusable constraints, etc.

.. _ug_build_system_targets_inheritance:

Inheritance and the ``default`` target
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Importantly, other targets in the same core do *not* inherit the contents of the ``default`` target automatically.
To achieve such inheritance behavior, FuseSoC provides a flexible inheritance mechanism, based on YAML anchors/references, YAML ``<<`` `merge operator <https://yaml.org/type/merge.html>`_, and a FuseSoC-specific list append feature.

The :ref:`blinky.core <ug_build_system_cb_blinky_full>` shows the recommended template to inherit configuration between targets.

#. Add ``&default`` after the ``default:`` text.
   This defines a YAML anchor named ``default``, which can be referenced later in the file.
#. Add a line ``<<: *default`` to the target where you want to inherit from ``default`` (the ``sim`` and ``synth`` targets in the example code).
   This line will effectively "copy over" all configuration under the ``default`` target.

As always with inheritance the interesting questions are around overriding behavior.

* Settings (keys) given in the target which inherits from ``default`` override the keys in ``default``.
  For example, the ``toplevel`` key in the ``sim`` target is overridden to be ``tb``.
  Note that no merging of setting data structure is performed.
* For settings which are lists, for example the ``filesets`` key, FuseSoC provides a way to combine lists by adding ``_append`` to the name of the key.

  This behavior is best explained by example.
  The ``filesets`` list in the ``default`` target consists of a single item, ``rtl``.
  The ``sim`` target wants to append the item ``tb`` (a file set with testbench files) to the list.
  To do so, it specifies the special ``filesets_append`` key with a partial list.
  When evaluating the core file, FuseSoC appends the contents of ``sim.fileset_append`` at the end of ``default.fileset`` to form a list with two items: ``rtl``, and ``tb``.
  The same behavior works for all lists in core files.
