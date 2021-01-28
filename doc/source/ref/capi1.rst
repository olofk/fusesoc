.. _ref_capi1:

******************
CAPI1 (deprecated)
******************

.. _type_definitions:

Type definitions
================

.. _File:

File
----

File objects consist of a mandatory file name, with path relative to the
core root. Extra options can be specified as a comma-separated list
enclosed in ``[]`` after the file name. Options are either boolean (``option``)
or has a value (``option=value``). No white-space is allowed anywhere in the
file object.

The following options are defined:

-  **file_type :** Value can be any type defined in `File
   types <#FileTypes>`__

-  **is_include_file :** Boolean value to indicate this should be
   treated as an include file

-  **logical_name :** Indicate that the file belongs to a logical unit
   (e.g. VHDL Library) with the name set by the value

-  **copyto :** Indicate that the file should be copied to a new
   location relative to the work root.

Example:
``rtl/verilog/uart_defines.v[file_type=verilogSource,is_include_file]``

Example: ``data/mem_init_file.bin[copyto=out/boot.bin]``

.. _FileList:

FileList
--------

Space-separated list of `File <#File>`__

Each element in the list is first subjected to the expansion according
to `PathList <#PathList>`__ and then parsed as a `File <#File>`__

.. _PathList:

PathList
--------

Space-separated list of paths

Each element in the list is subjected to expansion of environment
variables and ``~`` to home directories

.. _SimulatorList:

SimulatorList
-------------

List of supported simulators. Allowed values are ghdl, icarus, isim,
modelsim, vcs, verilator, xsim

.. _SourceType:

SourceType
----------

Language used for Verilator testbenches. Allowed values are C, CPP or
systemC

.. _StringList:

StringList
----------

Space-separated list of strings

.. _VlnvList:

VlnvList
--------

Space-separated list of VLNV tags

Each element is treated as a VLNV element with an optional version range

Example:

.. code-block ::

   librecores.org:peripherals:uart16550:1.5 >=::simple_spi:1.6
   mor1kx =::i2c:1.14``

.. _FileTypes:

File types
==========

The following valid file types are defined: PCF, QIP, SDC, UCF, BMM,
tclSource, user, verilogSource, verilogSource-95, verilogSource-2001,
verilogSource-2005, systemVerilogSource, systemVerilogSource-3.0,
systemVerilogSource-3.1, systemVerilogSource-3.1a, vhdlSource,
vhdlSource-87, vhdlSource-93, vhdlSource-2008, xci, xdc

.. _sections:

Sections
========

.. _fileset:

fileset
-------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - file_type
     - String
     - Default file type of the files in fileset

   * - files
     - `FileList <# FileList>`__
     - List of files in fileset

   * - is_include_file
     - String
     - Specify all files in fileset as include
       files

   * - logical_name
     - String
     - Default logical_name (e.g. library) of the
       files in fileset

   * - scope
     - String
     - Visibility of fileset (private/public).
       Private filesets are only visible when
       this core is the top-level. Public
       filesets are visible also for cores that
       depend on this core. Default is public

   * - usage
     - `StringList <#StringList>`__
     - List of tags describing when this fileset
       should be used. Can be general such as sim
       or synth, or tool-specific such as
       quartus, verilator, icarus. Defaults to
       *sim synth*.


.. _ghdl:

ghdl
----

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - analyze_options
     - `StringList <#StringList>`__
     - Extra GHDL analyzer options

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - run_options
     - `StringList <#StringList>`__
     - Extra GHDL run options


.. _icarus:

icarus
------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - iverilog_options
     - `StringList <#StringList>`__
     - Extra Icarus verilog compile options


.. _icestorm:

icestorm
--------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - arachne_pnr_options
     - `StringList <#StringList>`__
     - arachne-pnr options

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - pcf_file
     - `FileList <#FileList>`__
     - Physical constraint file

   * - top_module
     - String
     - RTL top-level module

   * - yosys_synth_options
     - `StringList <#StringList>`__
     - Additional options for the ``synth_*`` commands in yosys


.. _ise:

ise
---

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - device
     - String
     - FPGA device identifier

   * - family
     - String
     - FPGA device family

   * - package
     - String
     - FPGA device package

   * - speed
     - String
     - FPGA device speed grade

   * - tcl_files
     - `FileList <#FileList>`__
     - Extra TCL scripts

   * - top_module
     - String
     - RTL top-level module

   * - ucf_files
     - `FileList <#FileList>`__
     - UCF constraint files


.. _isim:

isim
----

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - isim_options
     - `StringList <#StringList>`__
     - Extra Isim compile options


.. _main:

main
----

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - backend
     - String
     - Backend for FPGA implementation

   * - component
     - `PathL ist <# PathLi st>`__
     - Core IP-Xact component file

   * - depend
     - `VlnvList <#VlnvList>`__
     - Common dependencies

   * - description
     - String
     - Core description

   * - name
     - String
     - Component name

   * - patches
     - `StringList <#StringList>`__
     - FuseSoC-specific patches

   * - simulators
     - `SimulatorList <#SimulatorList>`__
     - Supported simulators. Valid values are
       icarus, modelsim, verilator, isim and
       xsim. Each simulator have a dedicated
       section desribed elsewhere in this
       document


.. _modelsim:

modelsim
--------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - vlog_options
     - `StringList <#StringList>`__
     - Additional arguments for vlog

   * - vsim_options
     - `StringList <#StringList>`__
     - Additional arguments for vsim


.. _parameter:

parameter
---------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - datatype
     - String
     - Data type of argument (int, str, bool,
       file

   * - default
     - String
     - Default value of argument

   * - description
     - String
     - Parameter description

   * - paramtype
     - String
     - Type of parameter (plusarg, vlogparam,
       generic, cmdlinearg

   * - scope
     - String
     - Visibility of parameter. Private
       parameters are only visible when this core
       is the top-level. Public parameters are
       visible also when this core is pulled in
       as a dependency of another core


.. _quartus:

quartus
-------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - device
     - String
     - FPGA device identifier

   * - family
     - String
     - FPGA device family

   * - qsys_files
     - `FileList <#FileList>`__
     - Qsys IP description files

   * - quartus_options
     - String
     - Quartus command-line options

   * - sdc_files
     - `FileList <#FileList>`__
     - SDC constraint files

   * - tcl_files
     - `FileList <#FileList>`__
     - Extra script files

   * - top_module
     - String
     - RTL top-level module


.. _rivierapro:

rivierapro
----------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - vlog_options
     - `StringList <#StringList>`__
     - Additional arguments for vlog

   * - vsim_options
     - `StringList <#StringList>`__
     - Additional arguments for vsim


.. _scripts:

scripts
-------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - post_impl_scripts
     - `StringList <#StringList>`__
     - Scripts to run after backend
       implementation

   * - post_run_scripts
     - `StringList <#StringList>`__
     - Scripts to run after simulations

   * - pre_build_scripts
     - `StringList <#StringList>`__
     - Scripts to run before building

   * - pre_run_scripts
     - `StringList <#StringList>`__
     - Scripts to run before running simulations

   * - pre_synth_scripts
     - `StringList <#StringList>`__
     - Scripts to run before backend synthesis


.. _trellis:

trellis
-------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - nextpnr_options
     - `StringList <#StringList>`__
     - nextpnr options

   * - top_module
     - String
     - RTL top-level module

   * - yosys_synth_options
     - `StringList <#StringList>`__
     - Additional options for the ``synth_*`` commands in yosys


.. _vcs:

vcs
---

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - vcs_options
     - `StringList <#StringList>`__
     - Extra vcs compile options


.. _verilator:

verilator
---------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - cli_parser
     - String
     - Select CLI argument parser. Set to
       *fusesoc* to handle parameter sections
       like other simulators. Set to
       *passthrough* to send the arguments
       directly to the verilated model. Default
       is *passthrough*

   * - define_files
     - `PathL ist <# PathLi st>`__
     - Verilog include files containing \`define
       directives to be converted to C #define
       directives in corresponding .h files
       (deprecated)

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - include_files
     - `FileList <#FileList>`__
     - Verilator testbench C include files

   * - libs
     - `PathL ist <# PathLi st>`__
     - External libraries linked with the
       generated model

   * - source_type
     - String
     - Testbench source code language (Legal
       values are systemC, C, CPP. Default is C)

   * - src_files
     - `FileList <#FileList>`__
     - Verilator testbench C/cpp/sysC source
       files

   * - tb_toplevel
     - `FileList <#FileList>`__
     - Testbench top-level C/C++/SC file

   * - top_module
     - String
     - verilog top-level module

   * - verilator_options
     - `StringList <#StringList>`__
     - Verilator build options


.. _verilog:

verilog
-------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - file_type
     - String
     - Default file type of the files in fileset

   * - include_files
     - `FileList <#FileList>`__
     - Verilog include files

   * - src_files
     - `FileList <#FileList>`__
     - Verilog source files for
       synthesis/simulation

   * - tb_include_files
     - `FileList <#FileList>`__
     - Testbench include files

   * - tb_private_src_files
     - `FileList <#FileList>`__
     - Verilog source files that are only used in
       the core’s own testbench. Not visible to
       other cores

   * - tb_src_files
     - `FileList <#FileList>`__
     - Verilog source files that are only used in
       simulation. Visible to other cores


.. _vhdl:

vhdl
----

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - src_files
     - `PathL ist <# PathLi st>`__
     - VHDL source files for simulation and
       synthesis


.. _vivado:

vivado
------

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - hw_device
     - String
     - FPGA device identifier

   * - part
     - String
     - FPGA device part

   * - top_module
     - String
     - RTL top-level module


.. _vpi:

vpi
---

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - include_files
     - `FileList <#FileList>`__
     - C include files for VPI library

   * - libs
     - `StringList <#StringList>`__
     - External libraries linked with the VPI
       library

   * - src_files
     - `FileList <#FileList>`__
     - C source files for VPI library


.. _xsim:

xsim
----

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - depend
     - `VlnvList <#VlnvList>`__
     - Tool-specific Dependencies

   * - xsim_options
     - `StringList <#StringList>`__
     - Extra Xsim compile options


.. _provider:

provider
--------

The provider section gives information on where to find the source code
for the core. If the provider section is missing, the core is assumed to
be local, with the directory of the .core file as the root directory.

.. list-table::
   :widths: 33 33 33
   :header-rows: 0


   * - Name
     - Type
     - Description

   * - name
     - String
     - The name option selects which provider
       backend to use. All other provider options
       are specific to the selected provider.
       Currently supported backends are github,
       git, opencores, submodule and url.

   * - cachable
     - boolean
     - If the cachable option is set to false,
       FuseSoc will unconditionally refetch the
       core even if it is found in the cache.
       Default is true


Provider-specific options:

.. _github:

github
~~~~~~

-  **user :** Name of the github user or organisation.

-  **repo :** Name of the GIT repository.

-  **version :** Name of the GIT ref (i.e. commit SHA, branch or tag) to use

.. _git:

git
~~~

-  **repo :** URL of the GIT repository.

-  **version :** Name of the GIT ref (i.e. commit SHA, branch or tag) to
   use

.. _opencores:

opencores
~~~~~~~~~

-  **repo_name :** Name of the opencores project. Can be found under
   Details on the project homepage.

-  **repo_root :** The sub directory in the repo that contains the files
   of interest. In most cases the value "trunk" is used to avoid pulling
   in tags and branches.

-  **revision :** The svn revision of the repository.

.. _url:

url
~~~

-  **url :** URL of the core file (or archive).

-  **filetype :** File type (zip, tar, simple).

.. _known_issues:

Known issues
============

1. Spaces are not allowed anywhere in the paths.
