# FuseSoC

[![CI status](https://github.com/olofk/fusesoc/workflows/CI/badge.svg)](https://github.com/olofk/fusesoc/actions?query=workflow%3ACI)
[![image](https://img.shields.io/pypi/dm/fusesoc.svg?label=PyPI%20downloads)](https://pypi.org/project/fusesoc/)
[![LibreCores](https://www.librecores.org/olofk/FuseSoC/badge.svg?style=flat)](https://www.librecores.org/olofk/FuseSoC)

## Introduction

FuseSoC is an award-winning package manager and a set of build tools for
HDL (Hardware Description Language) code.

Its main purpose is to increase reuse of IP (Intellectual Property)
cores and be an aid for creating, building and simulating SoC solutions.

FuseSoC makes it easier to

-   reuse existing cores
-   create compile-time or run-time configurations
-   run regression tests against multiple simulators
-   port designs to new targets
-   let other projects use your code
-   set up continuous integration

To learn more about FuseSoC head over to the
[User Guide](https://fusesoc.readthedocs.io/en/stable/user).

## Getting started

### Installing the latest release

FuseSoC works on Linux, Windows, and macOS. It is written in Python and can be
installed like any other Python package through "pip". Please refer to the
full list of system requirements and installation instructions in the
[Installation section in the User Guide](https://fusesoc.readthedocs.io/en/stable/user/installation.html).

### Quick start

To check if FuseSoC is working, and to get an initial feeling for how FuseSoC
works, you can try to simulate a simple hardware design from our core libray.

First, create and enter an empty workspace

    mkdir workspace
    cd workspace

Install the FuseSoc base library into the workspace

    fusesoc library add fusesoc-cores https://github.com/fusesoc/fusesoc-cores

Get a list of cores found in the workspace

    fusesoc core list

If you have any of the supported simulators installed, you can try to
run a simulation on one of the cores as well. For example,
`fusesoc run --target=sim i2c` will run a regression test on the core
i2c with Icarus Verilog. If you want to try another simulator instead,
add e.g. `--tool=modelsim` or `--tool=xcelium` between `run` and `i2c`.

`fusesoc --help` will give you more information on commands and switches.

Did it work? Great! FuseSoC can be used to create FPGA images, perform
linting, manage your IP libraries or do formal verification as well.
Check out the [online documentation](https://fusesoc.readthedocs.io/en/stable/)
documentation to learn more about creating your own core files and using
existing ones. If it didn't work, please get in touch (see below).

## Next steps

A good way to get your first hands-on experience with FuseSoC is to
contribute to the [LED to Believe](https://github.com/fusesoc/blinky)
project. This project aims to used FuseSoC to blink a LED on every
available FPGA development board in existence. There are already around
40 different boards supported. If your board is already supported,
great, then you can run your first FuseSoC-based design. If it's not
supported, great, you now have the chance to add it to the list of
supported boards. Either way, head over to [LED to
Believe](https://github.com/fusesoc/blinky) to learn more and see how to
go from a blinking LED to running a RISC-V core on an FPGA.

## Need help?

FuseSoC comes with extensive
[online documentation](https://fusesoc.readthedocs.io/en/stable/index.html).

For quick communication with the active developers, feel free to join us at the
[FuseSoC chat](https://gitter.im/librecores/fusesoc).

If you have found an issue, or want to know more about currently known problems,
check out the
[issue tracker on GitHub](https://github.com/olofk/fusesoc/issues).

If you are looking for professional paid support, we are happy to
provide feature additions, bug fixes, user training, setting up core
libraries, migrating existing designs to FuseSoC and other things.
Please contact <olof.kindgren@gmail.com> for more information.

## Contributing to FuseSoC

FuseSoC is developed by an active and friendly community, and you're welcome to
join! You can read more about setting up a development environment in our
[Developer's Guide](https://fusesoc.readthedocs.io/en/latest/dev/index.html).

You can file bug reports and propose changes in the [olofk/fusesoc repository on GitHub](https://github.com/olofk/fusesoc).

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

## License

FuseSoC is licensed under the permissive 2-clause BSD license, freely allowing
use, modification, and distribution of FuseSoC for all kinds of projects.
Please refer to the [LICENSE](LICENSE) file for details.
