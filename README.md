# FuseSoC

[![CI status](https://github.com/olofk/fusesoc/workflows/CI/badge.svg)](https://github.com/olofk/fusesoc/actions?query=workflow%3ACI)

[![image](https://img.shields.io/pypi/dm/fusesoc.svg?label=PyPI%20downloads)](https://pypi.org/project/fusesoc/)

## Introduction

FuseSoC is an award-winning package manager and a set of build tools for
HDL (Hardware Description Language) code.

Its main purpose is to increase reuse of IP (Intellectual Property)
cores and be an aid for creating, building and simulating SoC solutions.

**FuseSoC makes it easier to**

-   reuse existing cores
-   create compile-time or run-time configurations
-   run regression tests against multiple simulators
-   Port designs to new targets
-   let other projects use your code
-   set up continuous integration

**FuseSoC is non-intrusive** Most existing designs doesn't need any
changes to work with FuseSoC. Any FuseSoC-specific patches can be
applied on the fly during implementation or simulation

**FuseSoC is modular** It can be used as an end-to-end flow, to create
initial project files for an EDA tool or integrate with your custom
workflow

**FuseSoC is extendable** Latest release support simulating with GHDL,
Icarus Verilog, Isim, ModelSim, Verilator and Xsim. It also supports
building FPGA images with Altera Quartus, project IceStorm, Xilinx ISE
and Xilinx Vivado. Support for a new EDA tool requires ~100 new lines
of code and new tools are added continuously

**FuseSoC is standard-compliant** Much effort has gone into leveraging
existing standards such as IP-XACT and vendor-specific core formats
where applicable.

**FuseSoC is resourceful** The standard core library currently
consisting of over 100 cores including CPUs, peripheral controllers,
interconnects, complete SoCs and utility libraries. Other core libraries
exist as well and can be added to complement the standard library

**FuseSoC is free software** It puts however no restrictions on the
cores and can be used to manage your company\'s internal proprietary
core collections as well as public open source projects

**FuseSoC is battle-proven** It has been used to successfully build or
simulate projects such as Nyuzi, Pulpino, VScale, various OpenRISC SoCs,
picorv32, osvvm and more.

Read more in the
[online](https://fusesoc.readthedocs.io/en/latest/index.html)
documentation, or get straight into business with the quick start below

## Getting started

Install latest stable version:

    sudo pip install fusesoc

or install latest development version from git:

    git clone https://github.com/olofk/fusesoc
    cd fusesoc
    sudo pip install -e .

FuseSoC should now be installed and ready to use. Next step is to add
some cores to use with FuseSoC. FuseSoC itself doesn\'t come with any
cores but there is a [FuseSoC base
library](https://github.com/fusesoc/fusesoc-cores) with a lot of useful
cores. In addition to that, many projects such as
[OpenTitan](https://github.com/lowRISC/opentitan),
[SweRVolf](https://github.com/chipsalliance/Cores-SweRVolf) and
[OpenPiton](https://github.com/PrincetonUniversity/openpiton) provide
their own core libraries.

If you have one of the supported simulators installed, and want to do a
quick check to see that it's working, follow the steps below, or look
at the
[tutorial](https://fusesoc.readthedocs.io/en/latest/user/tutorials/index.html)
in the [online](https://fusesoc.readthedocs.io/en/latest/index.html)
documentation for a more thorough introduction.

### Quick start

Create and enter an empty workspace

    mkdir workspace
    cd workspace

Install the FuseSoc base library into the workspace

    fusesoc library add fusesoc-cores https://github.com/fusesoc/fusesoc-cores

Get a list of cores found in the workspace

    fusesoc core list

If you have any of the supported simulators installed, you can try to
run a simulation on one of the cores as well. For example,
`fusesoc run --target=sim i2c` will run a regression test on the core
i2c with icarus verilog. If you want to try another simulator instead,
add e.g. `--tool=modelsim` or `--tool=xcelium` between [run]{.title-ref}
and [i2c]{.title-ref}.

`fusesoc --help` will give you more information on commands and
switches.

Did it work? Great! FuseSoC can be used to create FPGA images, perform
linting, manage your IP libraries or do formal verification as well.
Check out the
[online](https://fusesoc.readthedocs.io/en/latest/index.html)
documentation and
[tutorial](https://fusesoc.readthedocs.io/en/latest/user/tutorials/index.html)
to learn more about creating your own core files and using existing
ones. If it didn't work, please [get in touch](#get-in-touch)

## Next steps

A good way to get your first hands-on experience with FuseSoC is to
contribute to the [LED to Believe](https://github.com/fusesoc/blinky)
project. This project aims to used FuseSoC to blink a LED on every
available FPGA development board in existence. There are already around
40 different boards supported. If you\'re board is already supported,
great, then you can run your first FuseSoC-based design. If it\'s not
supported, great, you now have the chance to add it to the list of
supported boards. Either way, head over to [LED to
Believe](https://github.com/fusesoc/blinky) to learn more and see how to
go from a blinking LED to running a RISC-V core on an FPGA.

## Need help? {#get-in-touch}

The [online](https://fusesoc.readthedocs.io/en/latest/index.html)
documentation contains a
[tutorial](https://fusesoc.readthedocs.io/en/latest/user/tutorials/index.html)
as well as information for users and developers of cores, or FuseSoC
itself. For some quick communication with the active developers, feel
free to join us at the [FuseSoC
chat](https://gitter.im/librecores/fusesoc). If you have found an issue,
or want to know more about currently known problems, check out the
[issue tracker](https://github.com/olofk/fusesoc/issues).

If you are looking for professional paid support, we are happy to
provide feature additions, bug fixes, user training, setting up core
libraries, migrating existing designs to FuseSoC and other things.

Please contact <olof.kindgren@gmail.com> for more info

## Further reading

-   A Scalable Approach to IP Management with FuseSoC paper and slides
    from OSDA 2019 <https://osda.gitlab.io/19/kindgren.pdf>
    <https://osda.gitlab.io/19/kindgren-slides.pdf>
-   Antmicro blog post on how to use FuseSoC as a linter
    <https://antmicro.com/blog/2020/04/systemverilog-linter-and-formatter-in-fusesoc/>
-   FuseSoC-related posts on the Tales from Beyond the Register Map blog
    <http://olofkindgren.blogspot.com/search/label/FuseSoC>
-   Presentation from Latch-Up Portland 2019
    <https://www.youtube.com/watch?v=7eWRAOK9mns>
-   Presentation from WOSH 2019
    <https://www.youtube.com/watch?v=HOFYplIBSWM>
-   Presentation from ORConf 2017
    <https://www.youtube.com/watch?v=iPpT9k_H67k>
-   Presentation from ORConf 2016
    <https://www.youtube.com/watch?v=pKlJWe_HKPM>
