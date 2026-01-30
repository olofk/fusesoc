.. _ug_build_system_variables:

Variables: Flexibility in Cores
==================================

Variables in FuseSoC are global string, int, or boolean variables that influence build dependency resolution.
Variables can be used in multiple :term:`core files <core file>` to replace $ tagged variables with a value defined at the top level, or via the CLI.
For example, generators using parameters such as PROTOCOL or FREQUENCY can be configured differently, even when they do not exist in the same core as your toplevel.

Facts about variables:

* Variables are global string, int, or boolean variables.
* Variables are global, i.e. they apply to the whole build.
* All cores see the same variables under the same name.
* A valid variable name starts with a letter, and consists only of letters from the English alphabet, numbers, and the underscore (``_``).
* Variable names are case-sensitive.
* It is recommended to use lower-case letters only.
* Variables are very similar to flags

Setting variables
-----------------

User-defined variables can be set as a dict of key/value pairs in the variables section of a target, or they can be applied on the command line, using the ``--var`` argument to ``fusesoc run``.
Failing to define a variable that is used in a core file will result in an error.
Examples:

.. code-block:: bash

  # Set the variable "frequency" to "100MHz".
  fusesoc run --var "frequency=100MHz" fusesoc:examples:varexample:1.0.0

  # Set two variables, "frequency" and "protocol".
  fusesoc run --var "frequency=100MHz" --var "protocol=AXI4" fusesoc:examples:varexample:1.0.0


The ``--var`` argument can be used multiple times to set multiple variables.


.. note::

  Order matters!
  The FuseSoC command line is "context sensitive."
  Place the ``--var`` argument after the ``run`` command, but before the name of the core you are building.

Default values for variables can be set directly in the variables section of a target, like this.

.. code-block:: yaml

   # An excerpt from a core file.
   targets:
     sim:
       # ...
       variables:
         frequency : 250MHz # Build the design to run at 250MHz by default
         protocol: AXI4  # Use AXI4 to for our generated registers by default

Using variables
-----------

Variables can be used in :term:`core files <core file>` to effect the value of a CAPI2 key-value pair.

* To set a value in a CAPI2 string, prefix the variable name with a dollar sign (``$``) and place it where you would normally place a your CAPI2 value.
* Variables can be used in string, int, and boolean CAPI2 values.

The following example shows how to use variables in a core file.

.. code-block:: yaml

   # An excerpt from a core file.
   name: "fusesoc:examples:varexample"

   filesets:
     module:
     depend:
       - fusesoc:examples:my_generator_core
     files:
       - rtl/module.sv
      file_type: systemVerilogSource

   generators:
     my_generator:
       generator: my_generator_class
       parameters:
         PROTOCOL : $protocol  # Use the protocol variable to set the PROTOCOL parameter

   targets:
     default: &default
       filesets: [module]
       generate: [my_generator]


Variables can be used in many places in core files, and are designed to be inherently flexible.

To find all valid places where variables can be used, refer to the :ref:`ref_capi2`.
Expressions with variables can be used whenever the data type is ``StringWithUseFlags``, ``StringWithUseFlagsOrDict``, or ``StringWithUseFlagsOrList``.
