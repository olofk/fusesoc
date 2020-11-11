.. _ug_overview:

*********************
Understanding FuseSoC
*********************

The components of FuseSoC
=========================

FuseSoC is a package manager and a build system for HDL code.
The following sections explain the main concepts of FuseSoC, and how they work together to obtain, configure, and build hardware designs.

A fundamental entity in FuseSoC is a core.
Cores can be discovered by the FuseSoC package manager in local or remote locations, and combined into a full hardware design by the build system.

.. _ug_overview_cores:

FuseSoC's basic building block: cores
-------------------------------------

A **FuseSoC core** is a reasonably self-contained, reusable piece of IP, such as a FIFO implementation.
In other contexts, the same concept is called package (as in deb package, npm package, etc.), or programming library (a term which is used with a different meaning in FuseSoC).

A core in FuseSoC has a name, such as ``example:ip:fifo``.
The name and other information about the core, such as the list of (e.g. Verilog or VHDL) source files, is contained in a description file called the **core file**.
Core files have filenames ending in ``.core``.

A core can also have dependencies on other cores.
For example, a "FIFO core" can have a dependency on an "SRAM core."

Discover cores: the package manager
-----------------------------------

FuseSoC cores can be stored in many places, both locally and remote.
Finding cores, and producing a list of cores available to the user, is the job of the FuseSoC package manager.

To find cores, the FuseSoC package manager searches through a configurable set of **core libraries**.
A core library can be local or remote.
In the simplest case, a local core library is just a directory with cores, as it is common in many hardware projects.
To support more advanced cases of code re-use and discovery, FuseSoC can also use remote core libraries.
Remote core libraries can be a key enabler to IP re-use especially in larger corporate settings, or in free and open source silicon projects.

From cores to a whole system: the build system
----------------------------------------------

The FuseSoC build system resolves all dependencies between cores, starting from a top-level core.
A top-level core is technically just another FuseSoC core, but with a special meaning: it is the entry point into the design.
The output of the dependency resolution step is a list of source files and other metadata that an EDA tool needs to build (i.e. synthesize, simulate, lint, etc.) the top-level design.
The dependency resolution process can be influenced by constraints.
Constraints are effectively input variables to the build process, and capture things like the target of the build (e.g. simulation, FPGA synthesis, or ASIC synthesis), the EDA tool to be used (e.g. Verilator or Xilinx Vivado), and much more.

From a file list to a synthesized design: EDAlize it!
-----------------------------------------------------

After the build system has collected all source files and parameters of the design, it is time to hand off to the build tool, such as Xilinx Vivado for FPGA synthesis, Verilator for Verilog simulation, and so on.

How exactly the hand-off is performed is highly tool-dependent, but FuseSoC abstracts these differences away and users typically don't need to worry about them.
For example, in for Vivado, FuseSoC creates a Vivado project file and then executes Vivado to run through the synthesis and place and route steps until a final bitstream is produced.
For Verilator, it creates a Makefile and then calls Verilator to do its job.

FuseSoC supports many of the proprietary and open source EDA tools commonly used, and can be easily extended to support further ones.

Concepts of the FuseSoC build system
====================================

To understand how FuseSoC builds a design it is necessary to understand three basic concepts: targets, tool flows, and build stages.

.. _ug_overview_toolflows:

Tool flows
----------

A tool flow (often abbreviated to just "tool" or "EDA tool") is a piece of software operating on the design to analyze it, simulate it, transform it, etc.
Common categories of tools are simulators, synthesis tools, or static analysis tools.
For example, Verilator is a tool (a simulation and static analysis tool), as is Xilinx Vivado (an FPGA tool flow), or Synopsys Design Compiler (an ASIC synthesis tool).

FuseSoC tries its best to hide differences between tools to make switching between them as easy as possible.
For example, it often only requires a different command line invocation of FuseSoC to simulate a design with Synopsys VCS instead of with Icarus Verilog.
Of course, customization options for individual tools are still available for when they are needed.

.. _ug_overview_targets:

Targets
-------

Many things can be done with a hardware design:
it can be synthesized for an FPGA, it can be simulated, it can be analyzed by lint tools, and much more.
Even though all of these things operate on the same hardware design, there are differences:
design parameters (e.g. Verilog defines and parameters, or VHDL generics) are set differently, source files are added or substituted (e.g. a top-level testbench wrapper is added, or a behavioral model of an IP block is exchanged against a hard macro), etc.
In FuseSoC, a target is a group of such settings.
Users of FuseSoC can freely name targets.
Commonly used targets are one for simulation (typically called ``sim``), one for FPGA or ASIC synthesis (``synth``), and one for static analysis (``lint``).

.. _ug_overview_buildstages:

Build stages
------------

FuseSoC builds a design in three stages: setup, build, and run.

#. The **setup** stage.
   In this first step, the design is stitched together and prepared to be handed over to the tool flow.

   #. A dependency tree is produced, starting from the top-level core.
   #. Generators (special cores with dynamic behavior) are called.
      Cores produced by generators are inserted into the dependency tree as well.
   #. The dependency tree is resolved to produce a flattened view of the design.
      All design information is written into an EDAM file.
   #. Tool-flow specific setup routines are being called.

#. The **build** stage runs the tool flow until some form of output file has been produced.
#. The **run** stage somehow "executes" the build output.
   What this exactly means is highly tool flow dependent:
   for simulation flows, the simulation is executed.
   For static analysis (lint) flows, the lint tool is called and its output is displayed.
   For FPGA flows, the FPGA is programmed with the generated bitstream.
