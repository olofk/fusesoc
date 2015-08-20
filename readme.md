FuseSoC
=======

Introduction
------------
FuseSoC is a package manager and a set of build tools for HDL (Hardware Description Language) code.

Its main purpose is to increase reuse of IP (Intellectual Property) cores and be an aid for creating, building and simulating SoC solutions.

The package manager part can be seen as an apt, portage, yum, dnf, pacman for FPGA (Field-Programmable Gate Array)/ASIC (Application-Specific Integrated Circuit) IP cores.
A simple ini file describes mainly which files the IP core contains, which other IP cores it depends on and where FuseSoC shall fetch the code.


A collection of cores together with a top-level is called a system, and systems can be simulated or passed through the FPGA vendor tools to build a loadable FPGA image.

Currently FuseSoc supports simulations with ModelSim, Icarus Verilog, Verilator, Isim and Xsim. It also supports building FPGA images with Xilinx ISE and Altera Quartus

Cores
-----
FuseSoC does not contain any RTL (Register-Transfer Level) code or core description files. The official repository for FuseSoC compatible cores is https://github.com/openrisc/orpsoc-cores

Quick start
-----------
Install by cloning the repo, cd into fusesoc and run:

    autoreconf -i && ./configure && make
    sudo make install
    fusesoc init

Test your installation by running `fusesoc list-cores`. This should return the list of cores that FuseSoC has found.

If you have any of the supported simulators installed, you can try to run a simulation on one of the cores as well.
For example, `fusesoc sim --sim=icarus wb_sdram_ctrl` will run a regression test on the core wb_sdram_ctrl with icarus verilog.
If you also have Altera Quartus installed, you can try to build an example system - for example, `fusesoc build de0_nano`.

`fusesoc --help` will give you more information on commands and switches.

Further reading
---------------
A few tutorials using FuseSoC are available, but they are unfortunately all written before FuseSoC was renamed from orpsocv3:

http://web.archive.org/web/20150208222518/http://elec4fun.fr/2011-03-30-10-16-30/2012-08-22-20-50-31/or1200-barebox-on-de1
http://www.rs-online.com/designspark/electronics/eng/blog/booting-linux-on-a-de0-nano-with-orpsoc
