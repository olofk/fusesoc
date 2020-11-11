.. _ug_cli:

***************
Running FuseSoC
***************

FuseSoC is a command-line tool; this section explains how to use it.
The following content is aiming at users who already have a hardware design which uses FuseSoC.

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
