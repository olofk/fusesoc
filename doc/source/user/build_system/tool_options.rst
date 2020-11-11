.. _ug_build_system_tool_options:

Passing options to tools
========================

.. note::

   Refer to the :ref:`CAPI2 reference documentation <ref_capi2>` for a list of all available tools and their options.

FuseSoC abstracts away many differences between :term:`tools <tool>` and tries to provide sane defaults to build many designs out of the box with no further configuration required.
However, not all tool-specific details can be hidden.
At the same time, a certain level of tool-specific configurability is required to make full use of the features available in different tools.
Tool options are FuseSoC's way of customizing the way tools are used to build the design.

When calling ``fusesoc run`` on the command line any tool can be chosen to build a design with the ``--tool`` argument.
If no tool-specific configuration is given in the core file, the default tool configuration is used, which might or might not work for a given design.

To customize tool behavior a tool-specific section can be added to a core file at ``targets.TARGETNAME.tools.TOOLNAME``.
The name of the tool (``TOOLNAME``) must match FuseSoC's internal tool name (as passed to ``fusesoc run --tool=TOOLNAME``).
Depending on the tool different options are available.
Refer to the :ref:`CAPI2 reference documentation <ref_capi2>` for a list of all available tools and their options.

Most tool backends provide a way to set command line options to influence how the tools are called.
Typically, these keys are called ``BINARYNAME_options``, and they take a list of arguments as value.

The example below shows how tool options for Icarus Verilog (``icarus``) and Mentor ModelSim (``modelsim``) are set.

* The ``iverilog`` binary will be called with the ``-g2012`` command-line argument, indicating that SystemVerilog 2012 support should be enabled.
* Similarily, for ModelSim the argument ``-timescale=1ns/1ns`` will be passed to the ``vlog`` binary, which elaborates the design.

.. code-block:: yaml

   # A fragment from blinky.core
   # ...
   targets:
     sim:
       # ...
       tools:
         icarus:
           iverilog_options:
             - -g2012 # Use SystemVerilog-2012
         modelsim:
           vlog_options:
             - -timescale=1ns/1ns

.. note::

   Where to find tool-specific code in FuseSoC

   The tool-specific code is provided by the `edalize library <https://github.com/olofk/edalize>`_.
   Most files, such as project files and Makefiles, are templates within edalize and can be improved easily if necessary.
   Please open an issue at the `edalize issue tracker on GitHub <https://github.com/olofk/edalize/issues>`_ to suggest improvements to tool-specific code.
