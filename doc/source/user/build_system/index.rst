.. _ug_build_system:

******************************
Building a design with FuseSoC
******************************

The FuseSoC build system pieces together a hardware design from individual cores.

*Building a design* in FuseSoC means *calling a tool flow to produce some output, and execute it.*
Depending on the :term:`target` and the :term:`tool flow` chosen, the build process can do and produce very different things:
it could produce a runnable simulation, generate an FPGA bitstream, or run a static analysis tool to check for common programming errors.

Two steps are required to build a hardware design with FuseSoC:

#. Write one or more FuseSoC core description files.
   See :ref:`ug_build_system_core_files` for information on how to write core description files.
#. Call ``fusesoc run``.
   FuseSoC is a command-line tool and accessible through the ``fusesoc`` command.
   See :ref:`ug_cli` for information on how to use the ``fusesoc`` command.

Typically, FuseSoC support can be added to an existing design without changes to the directory structure or the source files.

The first three sections are recommended reading for all users of FuseSoC.
The first section :ref:`ug_build_system_core_files` is an introduction into :term:`core description files <core file>` and how to write them.
The second and third section, :ref:`ug_build_system_flow_options` and :ref:`ug_build_system_dependencies` look at how to customize what the (EDA) :term:`tools <tool>` are doing, and how cores can be combined to form a larger system.

.. note::

   Edalize has two different APIs for running EDA tool flows. The new flow API is described in :ref:`ug_build_system_flow_options` and will become the default API. However, not all Edalize backends have been converted to the new API, so the old tool API remains in use and is described in :ref:`ug_build_system_tool_options`. If FuseSoC encounters a `flow` key in the target, it will use the flow API. Otherwise it will fall back to the tool API

The subsequent sections are advanced topics, which are only relevant in some projects.

A full reference documentation on the CAPI2 core file format can be found in the section :ref:`ref_capi2`.

.. toctree::
   :maxdepth: 2
   :caption: In this section

   core_files.rst
   tool_options.rst
   dependencies.rst
   flags.rst
   generators.rst
   hooks.rst
   vpi.rst
