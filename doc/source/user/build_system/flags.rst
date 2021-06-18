.. _ug_build_system_flags:

Flags: constraints in dependencies
==================================

Flags in FuseSoC are global boolean variables that influence the dependency resolution and other aspects of the build.
Flags can be used in multiples places in :term:`core files <core file>` to take conditional actions.
For example, dependencies and files can be included depending on a flag, different toplevels can be selected, and much more.

Facts about flags:

* Flags are boolean variables, they are either "set" (true) or "unset" (false).
* Flags are global, i.e. they apply to the whole build.
  All cores see the same flags under the same name.
* A valid flag name starts with a letter, and consists only of letters from the English alphabet, numbers, and the underscore (``_``).
* Flag names are case-sensitive.
  It is recommended to use lower-case letters only.

Setting flags
-------------

Built-in flags are made available automatically.
User-defined flags can be set on the command line and override built-in flags.

Built-in flags
~~~~~~~~~~~~~~

When running ``fusesoc run`` some flags are automatically made available.

* ``tool_TOOLNAME``: A flag that is set only if a particular tool is used during the build process.
  ``TOOLNAME`` is replaced with the name of the used tool.
  For example, when building a design for Xilinx Vivado, ``tool_vivado`` will be set.
* ``target_TARGETNAME``: A flag that is set if a particular target is being built.
  ``TARGETNAME`` is replaced with the name of the target that is being built.
  For example, if the target ``synth`` is being built, the flag ``target_synth`` will be set.

User-defined flags
~~~~~~~~~~~~~~~~~~

Flags can be set when building a design with ``fusesoc run`` by passing the ``--flag`` argument.

To set a flag, specify only the flag name, or alternatively, prefix it with a plus, i.e. ``--flag FLAGNAME`` or ``--flag +FLAGNAME``.
To unset a flag, prefix the name of the flag with a hyphen, i.e. pass ``--flag -FLAGNAME``.

The ``--flag`` argument can be used multiple times to set or unset more than one flag.

Examples:

.. code:: bash

  # Set the flag "my_flag".
  fusesoc run --flag "my_flag" fusesoc:examples:blinky:1.0.0

  # Alternative: set the flag "my_flag"
  fusesoc run --flag "+my_flag" fusesoc:examples:blinky:1.0.0

  # Set two flags, "my_flag" and "my_other_flag"
  fusesoc run --flag "my_flag" --flag "my_other_flag" fusesoc:examples:blinky:1.0.0

  # Unset the flag "my_flag"
  fusesoc run --flag "-my_flag" fusesoc:examples:blinky:1.0.0

.. note::

  Order matters!
  The FuseSoC command line is "context sensitive."
  Place the ``--flags`` argument after the ``run`` command, but before the name of the core you are building.


Using flags
-----------

Flags can be used in :term:`core files <core file>` to influence the build as part of a CAPI2 expression.

* To test if a flag is set (true) and return ``my_string`` in that case, use the expression ``my_flag ? (my_string)``.
* To test if a flag is not set (false) and return ``my_string`` in that case, use the expression ``!my_flag ? (my_string)``.

.. note::
   **Quotation marks are required** for strings starting with an exclamation mark (``!``), but :ref:`always recommended <ug_build_system_core_files_yaml_intro>`.

CAPI2 expressions are *not* full ternary operators, i.e. no "else" branch is available.
Use two inverted expressions for if/else support.

The following use cases show some ways in which flags can be used in core description files.


Use case: Conditional dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flags can be used to influence which dependencies are included in a build.
A typical use case for this feature are dependencies which are tool-specific.

The following example shows how to depend on a core named ``fusesoc:examples:xilinx-fifo`` (presumably implementing a Xilinx-specific FIFO) only if the ``vivado`` tool is used.
Otherwise a core providing a tool-agnostic implementation is used.

.. code-block:: yaml

   # An excerpt from a core file.
   filesets:
     rtl:
       # ...
       depend:
         - "tool_vivado ? (fusesoc:examples:xilinx-fifo)"
         - "!tool_vivado ? (fusesoc:examples:generic-fifo)"


Use case: Conditionally include files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar to the way dependencies can be conditionally specified source files can also be included conditionally.

The following example shows how to include a file ``rtl/fifo_xilinx.sv`` only if Vivado is used, and ``rtl/fifo_generic.sv`` otherwise.

.. code-block:: yaml

   # An excerpt from a core file.
   filesets:
     rtl:
       # ...
       files:
         - "tool_vivado ? (rtl/fifo_xilinx.sv)"
         - "!tool_vivado ? (rtl/fifo_generic.sv)"


Use case: Conditional filesets in a target
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use flags in CAPI2 expressions in the ``targets.TARGETNAME.filesets`` block to conditionally include file sets.

The code snippet below shows how to include a fileset ``verilator_tb`` only if the ``verilator`` tool is used;
otherwise the fileset ``any_other_tool_tb`` is included.

.. code-block:: yaml

   # An excerpt from a core file.
   targets:
     # ...
     tb:
       # ...
       filesets:
         # Always include the rtl and tb filesets.
         - "rtl"
         - "tb"
         # Include the verilator_tb fileset only if verilator is used.
         - "tool_verilator ? (verilator_tb)"
         # Include the any_other_tool_tb fileset for all other tools.
         - "!tool_verilator ? (any_other_tool_tb)"


Use case: Conditionally choose a toplevel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Flags can also be used to choose the name a design toplevel based on certain conditions.

In the following code snippet, the user-defined flag ``experimental_toplevel`` is used to switch between two toplevels.

.. code-block:: yaml

   # An excerpt from a core file.
   name: "fusesoc:examples:my_core"
   targets:
     # ...
     synth:
       toplevel:
         - "experimental_toplevel ? (top_experimental)"
         - "!experimental_toplevel ? (top_production)"
       # ...

With this setup in place users can choose which toplevel they want to build by passing the ``--flag`` command line argument to ``fusesoc``, as illustrated in the following example.

.. code-block:: bash

  # Build top_experimental
  fusesoc run --flag experimental_toplevel --target synth fusesoc:examples:my_core

  # Build top_production
  fusesoc run --target synth fusesoc:examples:my_core

Further use cases
~~~~~~~~~~~~~~~~~

Flags can be used in more places than shown here.
To find all valid places where flags can be used, refer to the :ref:`ref_capi2`.
Expressions with flags can be used whenever the data type is ``StringWithUseFlags``, ``StringWithUseFlagsOrDict``, or ``StringWithUseFlagsOrList``.
