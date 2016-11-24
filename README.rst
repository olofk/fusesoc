FuseSoC
=======

.. image:: https://travis-ci.org/olofk/fusesoc.svg?branch=master
    :target: https://travis-ci.org/olofk/fusesoc

.. image:: https://ci.appveyor.com/api/projects/status/bg3tutcube9x0fgs/branch/master?svg=true
    :target: https://ci.appveyor.com/project/olofk/fusesoc/branch/master

Introduction
------------
FuseSoC is a package manager and a set of build tools for HDL (Hardware Description Language) code.

Its main purpose is to increase reuse of IP (Intellectual Property) cores and be an aid for creating, building and simulating SoC solutions.

**FuseSoC makes it easier to**

- reuse existing cores

- create compile-time or run-time configurations

- run regression tests against multiple simulators

- Port designs to new targets

- let other projects use your code

- set up continuous integration 

**FuseSoC is non-intrusive** Most existing designs doesn't need any changes to work with FuseSoC. Any FuseSoC-specific patches can be applied on the fly during implementation or simulation

**FuseSoC is modular** It can be used as an end-to-end flow, to create initial project files for an EDA tool or integrate with your custom workflow

**FuseSoC is extendable** Latest release support simulating with GHDL, Icarus Verilog, Isim, ModelSim, Verilator and Xsim. It also supports building FPGA images with Altera Quartus, project IceStorm, Xilinx ISE and Xilinx Vivado. Support for a new EDA tool requires ~100 new lines of code and new tools are added continuously

**FuseSoC is standard-compliant** Much effort has gone into leveraging existing standards such as IP-XACT and vendor-specific core formats where applicable.

**FuseSoC is resourceful** The standard core library currently consisting of over 100 cores including CPUs, peripheral controllers, interconnects, complete SoCs and utility libraries. Other core libraries exist as well and can be added to complement the standard library

**FuseSoC is free software** It puts however no restrictions on the cores and can be used to manage your company's internal proprietary core collections as well as public open source projects

**FuseSoC is battle-proven** It has been used to successfully build or simulate projects such as Nyuzi, Pulpino, VScale, various OpenRISC SoCs, picorv32, osvvm and more.

Read more in the online_ documentation, or get straight into business with the quick start below

Quick start
-----------

Install latest stable version:

::

   sudo pip install fusesoc

Install latest development version from git:

::
   
   git clone https://github.com/olofk/fusesoc
   cd fusesoc
   sudo pip install -e .

FuseSoC should now be installed. Next step is to download the standard IP core libraries, which contain over 100 Open Source IP cores.

*FuseSoC is currently in a transition phase and will prompt for the old standard library (* orpsoc-cores_ *) in addition to the new one (* fusesoc-cores_ *)*

::
   
   fusesoc init

Test your installation by running ``fusesoc list-cores``. This should return the list of cores that FuseSoC has found.

If you have any of the supported simulators installed, you can try to run a simulation on one of the cores as well.
For example, ``fusesoc sim --sim=icarus wb_sdram_ctrl`` will run a regression test on the core wb_sdram_ctrl with icarus verilog.
If you also have Altera Quartus installed, you can try to build an example system - for example, ``fusesoc build de0_nano``.

``fusesoc --help`` will give you more information on commands and switches.

Did it work? Great! Check out the online_ documentation to learn more about creating your own core files and using existing ones. If it didn't work, please file a `bug report`_


Documentation
-------------

Documentation can be viewed online_. To manually create HTML documentation from the asciidoc sources, run ``cd doc && make`` from the repo root

Further reading
---------------
A few tutorials using FuseSoC are available, but they are unfortunately all written before FuseSoC was renamed from orpsocv3:

http://web.archive.org/web/20150208222518/http://elec4fun.fr/2011-03-30-10-16-30/2012-08-22-20-50-31/or1200-barebox-on-de1

http://www.rs-online.com/designspark/electronics/eng/blog/booting-linux-on-a-de0-nano-with-orpsoc

There is also some FuseSoC-related articles and extended release information on my blog_

.. _blog: https://olofkindgren.blogspot.com/search/label/FuseSoC
.. _online: doc/fusesoc.adoc
.. _orpsoc-cores: https://github.com/openrisc/orpsoc-cores
.. _fusesoc-cores: https://github.com/fusesoc/fusesoc-cores
.. _`bug report`: https://github.com/olofk/fusesoc/issues
