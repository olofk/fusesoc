.. _ug_cli:

***************
Running FuseSoC
***************

FuseSoC is a command-line tool; this section explains how to use it.
The following content is aimed at users who already have a hardware design which uses FuseSoC.

Build a design
==============

The ``fusesoc run`` group of commands is used to setup, build, and (if possible) run a design.
The exact actions taken by the individual steps depend on the toolflow.

::

    usage: fusesoc run [-h] [--no-export] [--build-root BUILD_ROOT] [--setup] [--build] [--run] [--target TARGET] [--tool TOOL] [--flag FLAG] [--system-name SYSTEM_NAME] system ...

    positional arguments:
      system                Select a system to operate on
      backendargs           arguments to be sent to backend

    optional arguments:
      -h, --help            show this help message and exit
      --no-export           Reference source files from their current location instead of exporting to a build tree
      --build-root BUILD_ROOT
                            Output directory for build. Defaults to build/$VLNV
      --setup               Execute setup stage
      --build               Execute build stage
      --run                 Execute run stage
      --target TARGET       Override default target
      --tool TOOL           Override default tool for target
      --flag FLAG           Set custom use flags. Can be specified multiple times
      --system-name SYSTEM_NAME
                            Override default VLNV name for system

When FuseSoC is invoked with the run command, it will create an empty working directory called `work_root` internally, where it by default will create all project files, copy all used source files, build and optionally run the project.

Setup, build and run
--------------------

The process of running EDA tools is divided into three steps called *setup*, *build* and *run*. The *setup* stage creates the working directory and all project files. The *build* stage runs one or more EDA tools to build an artifact, e.g. a GDS, simulation model or FPGA image. The *run* stage is only implemented for some tool flows, such as simulation flows where it runs the simulation. Some FPGA flows uses the *run* stage to program an FPGA device.

Normally FuseSoC runs all three stages, but if the `--setup` flag is added, it will stop after the setup stage and if the `--build` flag is set it will stop after the build stage. Many of the newer backends don't need these flags and will instead only run setup or build when input files or options have changed.

Work root
---------
`work_root` is a private working directory and should not be shared between different builds. It is however perfectly fine to reuse the working directory for e.g. running several simulations using different runtime options as long as the build-time options and source files are not modified.

By default, FuseSoC will use `build/<sanitized VLNV>/<target>`, where `<sanitized VLNV>` is the top-level VLNV with underscore instead of colon as the separator. For the Flow API, `<target>` is just the name of the target in the core description file, e.g. `sim`. For the old Tool API, it is a combination of target name and the tool backend, e.g. `sim-verilator`. The work root directory can be changed with the `--work-root` option.

Exporting source files
----------------------

The standard behavior for FuseSoC is to copy all used source files into a subdirectory of the work root. This has three advantages. The work root is self-contained with all the source files and can be copied elsewhere for archival purposes or to build on another machine. No stray files are picked up by mistake from the original source directories. It is always possible to know from exactly which files a build was created. Despite this, there are situations where it is preferable to reference the source files from their original location. This can be done by adding the `--no-export` flag.
