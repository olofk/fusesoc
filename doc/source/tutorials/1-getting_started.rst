FuseSOC: Getting Started
========================

Some time ago I neeeded to build an emulated GPS device for a project. I reckoned it was easiest to do so with an old FPGA board and since this is turned out to be a pretty straight-forward SoC I also realized it would serve well as a tutorial. So here it is, the first tutorial on getting started with building systems using FuseSoC.

To help with the project I got my trusty old DE0 Nano board, but most of the tutorial requires no hardware at all, and some parts will work on other hardware with only minor modifications.

Background
----------

The GPS I intend to emulate has two outputs. One is a signal that changes polarity once a second emulating a 0.5Hz clock signal. This is called a PPS (Pulse Per Second) signal in GPS parlour. There are multiple variants of the PPS scheme, in some cases it is a short pulse every second instead of just changing polarity, but we ignore those for now.

The second signal is a serial UART data signal that transmits an ASCII message at 4800 baud rate every second. The data sent on the serial link uses the `NMEA protocol <http://www.gpsinformation.org/dale/nmea.htm>`__. While many messages are defined in the NMEA protocol, this particular device emulator will only implement the ``$GPGGA`` message. Each message is sent some time (e.g. 200ms) after the positive edge on the PPS signal.

Both signals together will look something like this

.. raw:: html

   <!-- wavedrom gps signal graph source
   {signal: [
     {name: 'nmea', wave: '13..1.3..1.3..1.3..1.', data: ['$GPGGA...','$GPGGA...','$GPGGA...','$GPGGA...']},
     {name: 'pps', wave: '0....1....0....1....0'}
   ]}
   -->

.. figure:: http://wavedrom.craftware.info/rest/gen_image?type=svg&scale=1.0&c=34AClAFldAD2cyVX4n%2ByefOiEYt63aI8IHLdqN3Cdv8qf5HXqNocbgFRnKx3wVJdHgenFvmyEUgZQOzjFvuEuBmQd6egQkNkuG8IgVkvYtSVZqVRxWIfZgHb61XLyyFMAAAAAABzbhnhdpHHiAAF1pgEAAAD8RWHfscRn%2BwI%3D
   :alt: gps signal graph

   gps signal graph

Alright, shouldn't be too hard. Let's get started with the coding.

Preparations
------------

Before we do anything, we need to install the required tools. First on the list is of course FuseSoC. This is pretty easy using the python pip package manager.

::

    pip install fusesoc

FuseSoC is now installed, but as with all package managers, they are not all that useful without actual packages. This will become evident if you run

::

    fusesoc list-cores

This should result in an empty list and a message saying ``ERROR: cores_root is not defined`` if you never had FuseSoC on your system before.

Luckily FuseSoC comes with two standard libraries (It should really only be one, but the transition has taken a bit longer than expected).

To download and register the standard libraries with FuseSoC run

::

    fusesoc init

Running fusesoc ``list-cores`` again should now result in a much larger list of cores.

During fusesoc init, FuseSoC has created a configuration file in ``$XDG_CONFIG_HOME/fusesoc/fusesoc.conf`` (``$XDG_CONFIG_HOME`` is normally set to ``~/.config`` on Linux systems and somewhere else, not sure to be honest, on Windows and MacOS)

The file will have two sections, one for each of the above mentioned libraries and looks like this

::

    [library.orpsoc-cores]
    sync-uri = https://github.com/openrisc/orpsoc-cores
    sync-type = git

    [library.fusesoc-cores]
    sync-uri = https://github.com/fusesoc/fusesoc-cores
    sync-type = git

Sections that start with library. describe a library. There are other types of sections (well, at least one more type) as well, but we will ignore that for now.

What we can see from the configuration file is that each library has a sync-uri and a sync-type option. FuseSoC uses these when a user runs fusesoc update to know how and where to get the latest version of the library.

The libraries themselves are found under ``$XDG_DATA_HOME/fusesoc`` (``$XDG_DATA_HOME`` is normally set to ``~/.local/share`` under Linux and somewhere else on other operating systems).

We never told FuseSoC explicitly where to find the libraries. The magic part here is that FuseSoC will look at each ``[library.<name>]`` section and search for a corresponding library under ``$XDG_DATA_HOME/fusesoc/<name>``. An explicit location can also be set for a library using the location option. We will do that soon, but let us first look at the contents of the libraries.

The fusesoc-cores library will contain a bunch of directories, each containing files ending with ``.core`` . These files are the heart and soul of FuseSoC and are called core description files. A core description file contains all the information FuseSoC needs to have about the core in order to run simulations on the core, build it for an FPGA target or use it as a depencency of another core. To get familiar with .core files, we can take a look at a simple one. Let's start with ``fusesoc-cores/uart16550/uart16550-1.5.5-r1.core``

.. code:: yaml

    CAPI=2:
    name : ::uart16550:1.5.5-r1
    description : UART 16550 transceiver

    filesets:
      rtl:
        files:
          - rtl/verilog/uart_defines.v: {is_include_file: true}
          - rtl/verilog/raminfr.v
          - rtl/verilog/uart_receiver.v
          - rtl/verilog/uart_regs.v
          - rtl/verilog/uart_rfifo.v
          - rtl/verilog/uart_sync_flops.v
          - rtl/verilog/uart_tfifo.v
          - rtl/verilog/uart_top.v
          - rtl/verilog/uart_transmitter.v
          - rtl/verilog/uart_wb.v
        file_type: verilogSource

    provider:
      name    : github
      user    : olofk
      repo    : uart16550
      version : v1.5.5

    targets:
      default:
        filesets: [rtl]

The information in the core description file is stored in the yaml format with an additional requirement that it must start with ``CAPI=2``. The : at the end of the first line is a compromise. It's not used for anything more than making this a valid yaml file.

Next line is the name. Names are specified in the VLNV (Vendor Library Name Version) format with ``:`` to separate the fields. FuseSoC allows vendor and library to be left empty, which is why many core names start with ``::.`` The VLNV format comes from IP-XACT, a standard that we hopefully will revisit in later tutorials. For now we can happily ignore that.

Description should be pretty self-explanatory.

Next up is the filesets section. Related source files are lumped together in filesets. There can for example be one fileset for the testbench and another one for the RTL implementation. This example only has a single fileset that is called rtl. The file ``uart_defines.v`` is noted to be an include file, i.e. a file that is included in other verilog files with the ``include`` statement. All files in the fileset are of the type ``verilogSource``.

Moving down we find a section called targets. Targets in core files are a bit like ``Makefile`` targets, and all settings specified in a specific target section will be used when that target is invoked. Only a single target, namely the default target, is defined here. default is a special target that is used when no explicit target is requested, and this is also the target that will be referenced when this core is used as a dependency of another core. More about dependency handling later. The only thing we do in the default target is to say that this target uses the rtl fileset that was defined above.

Ok, so the core description file references a bunch of files, but... there are no files to be seen anywhere. What's going on here? To answer that we need to look at the next section, the provider section. If a core description file has a provider section, it's called a remote core. If it hasn't, then we call it a local core. When a remote core is needed, FuseSoC will first look in its cache directory to see if it has already been downloaded (fetched). If not, it will look at the provider section to figure out how to fetch the source code. Once it is in the cache, it will use the cached version.

Before we start writing our own first core we will look at a slightly more complicated example.

Let's take a look at ``fusesoc-cores/i2c/i2c-1.14-r1.core`` which looks like this

.. code:: yaml

    CAPI=2:
    name : ::i2c:1.14-r1
    filesets:
      rtl_files:
        files:
          - rtl/verilog/i2c_master_bit_ctrl.v
          - rtl/verilog/i2c_master_byte_ctrl.v
          - rtl/verilog/i2c_master_defines.v: {is_include_file : true}
          - rtl/verilog/i2c_master_top.v
        file_type : verilogSource

      tb_files:
        depend:
          - ">=vlog_tb_utils-1.0"
          - wiredelay
        files:
          - bench/verilog/wb_master_model.v
          - bench/verilog/tst_bench_top.v
          - bench/verilog/i2c_slave_model.v
        file_type : verilogSource

    targets:
      default:
        filesets : [rtl_files]
      sim:
        default_tool : icarus
        filesets : [rtl_files, tb_files]
        toplevel : tst_bench_top

    provider:
      name : github
      user : olofk
      repo : i2c
      version : v1.14
      patches : [files/0001-add_vlog_tb_utils.patch]

Again, we see the ``CAPI=2`` header, name, filesets, target and the provider section. Let's focus on the differences from the previous example. In the filesets section, there are now two filesets. The one called ``tb_files`` also has an additional field called depend. This is where we enter the package management territory of FuseSoC. This means that the files in the ``tb_files`` fileset uses functionality from other cores and need to have them present when building the project. In this case it requires any version of a core named wiredelay, and at least version 1.0 of a core named ``vlog_tb_utils``. Running fusesoc list-cores will hopefully reveal that both these cores are present in the standard libraries.

In the target section there is also a new target called sim. This one has two options in addition to the previously mentioned filesets. ``default_tool`` decides which tool to use if the user doesn't explicitly selects a tool on the FuseSoC command-line. More on that later. The other option is toplevel. This identifies which verilog module or VHDL entity that should be used as the top-level instance when building the project. Commonly there is a single toplevel, but in some cases several toplevels must be set, in which case this will be defined as a list, e.g. ``[first_toplevel, second_toplevel]``.

A third difference is that patches option in the provider section. Sometimes when packaging third-party cores there might be aspects of the original code that does not work well with FuseSoC. By specifying diff files in the patches option, it is possible to apply patches to cores after they have been downloaded before they are stored in the FuseSoC cache. Common uses for this is to remove hard-coded file paths that clashes with FuseSoC directory layout or add useful features. In this case the patch adds support for functionality from the ``vlog_tb_utils`` core.

We are now almost ready to write our own core, but let's begin with running some examples related to the core we just looked at. Start by running ``fusesoc core-info``. There's not much information here, but we should be able to verify that it's indeed the core we looked at by checking the line starting with ``Core root``. We can also see that the FuseSoC core parser has found two targets, default and sim.

Next up we can run the testbench of the ``i2c`` core. Before doing this, create an empty directory that will be used as the workspace. For this tutorial we will use ``~/fusesoc_tutorial/workspace``. Enter the newly created workspace directory, make sure Icarus Verilog is installed and run ``fusesoc run --target=sim i2c``. This should run the testbench and finally output ``Testbench done``.

If we look at the beginning of the output from the command we will see

::

    INFO: Preparing ::vlog_tb_utils:1.1
    INFO: Downloading fusesoc/vlog_tb_utils from github
    INFO: Preparing ::wiredelay:0
    INFO: Preparing ::i2c:1.14-r1
    INFO: Downloading olofk/i2c from github

When we launched the simulation, we specified ``--target=sim``, which uses the ``targets/sim`` section in the core file. Going deeper down the rabbit hole, the sim section uses the tb\_files fileset and the tb\_files fileset depend on ``>=vlog_tb_utils-1.0`` and ``wiredelay``. The ``>=vlog_tb_utils-1.0`` requirement got us ``vlog_tb_utils:1.1``, which is the highest version to satisfy this requirement. This is also a remote core, which means that FuseSoC had to download it and put it in the cache before it could be used. wiredelay on the other hand is a local core and all the needed files are already present on the disk (Check core-info wiredelay to find out where the files are located). Also the i2c core was a remote core and had to be downloaded. You will now find the cached cores in ``$XDG_CACHE_HOME/fusesoc`` (normally ``~/.cache/fusesoc`` on Linux systems).

If another simulator is preferred, we can use that by adding a ``--tool=`` option on the command line, e.g. ``fusesoc run --target=sim --tool=modelsim i2c``

Looking at our workspace directory there will now be a directory called build containing a directory called ``i2c_1.14-r1``. Inside of that you fill find sim-icarus and src. src contains all the sources of the cores in the dependency tree (i.e. ``vlog_tb_utils``, ``wiredelay`` and ``i2c``). ``sim-icarus`` is the working directory of the simulation, meaning the directory where the simulator tool was launched from. There are a couple of files in there, and these will be revisited in later tutorials. The only thing to notice right now is that the directory itself is named after ``<target>-<tool>``.

Other simulators to try are isim, xsim or rivierapro. Be aware that not all tools work for all cores. Upon running a second simulation there should also not be any ``INFO: Downloading...`` messages as the dependencies are already cached.

Let's run another simulation, but this time we want to generated a VCD waveform file. Run ``fusesoc run --target=sim i2c --vcd``. Looking at the work directory now, there will also be a file called testlog.vcd which can be viewed with GTKWave or other VCD-compatible readers. One important thing to be aware of here is that the options specified after the core we want to run (i2c in this case) are options that are specified by the cores themselves. FuseSoC has no knowledge of a --vcd option but will just pass it along. In this case it's not even the i2c core that specifies the --vcd option, but the vlog\_tb\_utils core that we depend on. How this works will be explained later, but to know what options that is implemented for each tool, target and core combination run ``fusesoc run <core> --help``.

Running ``fusesoc run --help`` instead will reveal the options available for the run command and running ``fusesoc --help`` will show available commands and global options.

.. `Next tutorial: Writing a new core file <2-creating_a_core.rst>`__
