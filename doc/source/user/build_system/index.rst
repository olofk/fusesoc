.. _ug_build_system:

******************************
Building a design with FuseSoC
******************************

The FuseSoC build system pieces together a hardware design from individual cores.

*Building a design* in FuseSoC means *calling a tool flow to produce some output, and execute it.*
Depending on the :term:`target` and the :term:`tool flow` chosen, the build process can do and produce very different things:
it could produce a runnable simulation, an FPGA bitstream, or run a static analysis tool to check for common programming errors.

To build a hardware design with FuseSoC two steps are required:

#. Write one or multiple FuseSoC core description file(s).
   Read on in this section for information on how to do that.
#. Call ``fusesoc run``.
   FuseSoC is a command-line tool and accessible through the ``fusesoc`` command.
   See :ref:`ug_cli` for information on how to use the ``fusesoc`` command.

Typically, FuseSoC support can be added to an existing design without changes to the directory structure or the source files.
The following sections explain how to do it.

The first three sections are recommended reading for all users of FuseSoC.
The first section :ref:`ug_build_system_core_files` is an introduction into :term:`core description files <core file>` and how to write them.
The second and third section, :ref:`ug_build_system_tool_options` and :ref:`ug_build_system_dependencies` look at how to customize what the (EDA) :term:`tools <tool>` are doing, and how cores can be combined to form a larger system.

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
