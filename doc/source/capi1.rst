CAPI1 (deprecated)
==================


Type definitions
----------------

[[File]] File ~~~~ File objects consist of a mandatory file name, with
path relative to the core root. Extra options can be specified as a
comma-separated list enclosed in [] after the file name. Options are
either boolean (option) or has a value (option=value). No white-space is
allowed anywhere in the file object

The following options are defined:

-  *file_type :* Value can be any type defined in <<FileTypes, File
   types>>

-  *is_include_file :* Boolean value to indicate this should be treated
   as an include file

-  *logical_name :* Indicate that the file belongs to a logical unit
   (e.g. VHDL Library) with the name set by the value
-  *copyto :* Indicate that the file should be copied to a new location
   relative to the work root.

Example:
rtl/verilog/uart_defines.v[file_type=verilogSource,is_include_file]

Example: data/mem_init_file.bin[copyto=out/boot.bin]

[[FileList]] FileList ~~~~~~~~ Space-separated list of <>

Each element in the list is first subjected to the expansion according
to <> and then parsed as a <>

[[PathList]] PathList ~~~~~~~~ Space-separated list of paths

Each element in the list is subjected to expansion of environment variables and
   to home directories

[[SimulatorList]] SimulatorList ~~~~~~~~~~~~~ List of supported
simulators. Allowed values are ghdl, icarus, isim, modelsim, verilator,
xsim

[[SourceType]] SourceType ~~~~~~~~~~ Language used for Verilator
testbenches. Allowed values are C, CPP or systemC

[[StringList]] StringList ~~~~~~~~~~ Space-separated list of strings

[[VlnvList]] VlnvList ~~~~~~~~ Space-separated list of VLNV tags

Each element is treated as a VLNV element with an optional version range

Example: librecores.org:peripherals:uart16550:1.5 >=::simple_spi:1.6
mor1kx =::i2c:1.14

[[FileTypes]] File types ———-

The following valid file types are defined: PCF, QIP, SDC, UCF,
tclSource, user, verilogSource, verilogSource-95, verilogSource-2001,
verilogSource-2005, systemVerilogSource, systemVerilogSource-3.0,
systemVerilogSource-3.1, systemVerilogSource-3.1a, vhdlSource,
vhdlSource-87, vhdlSource-93, vhdlSource-2008, xci, xdc

Sections
--------

fileset ~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|file_type \| String \| Default file type of the
files in fileset \|files \| <<FileList,FileList>> \| List of files in
fileset \|is_include_file \| String \| Specify all files in fileset as
include files \|logical_name \| String \| Default logical_name
(e.g. library) of the files in fileset \|scope \| String \| Visibility
of fileset (private/public). Private filesets are only visible when this
core is the top-level. Public filesets are visible also for cores that
depend on this core. Default is public \|usage \|
<<StringList,StringList>> \| List of tags describing when this fileset
should be used. Can be general such as sim or synth, or tool-specific
such as quartus, verilator, icarus. Defaults to ‘sim synth’.
\|==============================

ghdl ~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|analyze_options \| <<StringList,StringList>> \|
Extra GHDL analyzer options \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|run_options \| <<StringList,StringList>> \|
Extra GHDL run options \|==============================

icarus ~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|iverilog_options \|
<<StringList,StringList>> \| Extra Icarus verilog compile options
\|==============================

icestorm ~~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|arachne_pnr_options \|
<<StringList,StringList>> \| arachne-pnr options \|depend \|
<<VlnvList,VlnvList>> \| Tool-specific Dependencies \|pcf_file \|
<<FileList,FileList>> \| Physical constraint file \|top_module \| String
\| RTL top-level module \|yosys_synth_options \|
<<StringList,StringList>> \| Additional options for the synth_\*
commands in yosys \|==============================

ise ~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|device \| String \| FPGA device identifier
\|family \| String \| FPGA device family \|package \| String \| FPGA
device package \|speed \| String \| FPGA device speed grade \|tcl_files
\| <<FileList,FileList>> \| Extra TCL scripts \|top_module \| String \|
RTL top-level module \|ucf_files \| <<FileList,FileList>> \| UCF
constraint files \|==============================

isim ~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|isim_options \| <<StringList,StringList>>
\| Extra Isim compile options \|==============================

main ~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|backend \| String \| Backend for FPGA
implementation \|component \| <<PathList,PathList>> \| Core IP-Xact
component file \|depend \| <<VlnvList,VlnvList>> \| Common dependencies
\|description \| String \| Core description \|name \| String \|
Component name \|patches \| <<StringList,StringList>> \|
FuseSoC-specific patches \|simulators \| <<SimulatorList,SimulatorList>>
\| Supported simulators. Valid values are icarus, modelsim, verilator,
isim and xsim. Each simulator have a dedicated section desribed
elsewhere in this document \|==============================

modelsim ~~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|vlog_options \| <<StringList,StringList>>
\| Additional arguments for vlog \|vsim_options \|
<<StringList,StringList>> \| Additional arguments for vsim
\|==============================

parameter ~~~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|datatype \| String \| Data type of argument
(int, str, bool, file \|default \| String \| Default value of argument
\|description \| String \| Parameter description \|paramtype \| String
\| Type of parameter (plusarg, vlogparam, generic, cmdlinearg \|scope \|
String \| Visibility of parameter. Private parameters are only visible
when this core is the top-level. Public parameters are visible also when
this core is pulled in as a dependency of another core
\|==============================

quartus ~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|device \| String \| FPGA device identifier
\|family \| String \| FPGA device family \|qsys_files \|
<<FileList,FileList>> \| Qsys IP description files \|quartus_options \|
String \| Quartus command-line options \|sdc_files \|
<<FileList,FileList>> \| SDC constraint files \|tcl_files \|
<<FileList,FileList>> \| Extra script files \|top_module \| String \|
RTL top-level module \|==============================

rivierapro ~~~~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|vlog_options \| <<StringList,StringList>>
\| Additional arguments for vlog \|vsim_options \|
<<StringList,StringList>> \| Additional arguments for vsim
\|==============================

scripts ~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|post_impl_scripts \| <<StringList,StringList>>
\| Scripts to run after backend implementation \|post_run_scripts \|
<<StringList,StringList>> \| Scripts to run after simulations
\|pre_build_scripts \| <<StringList,StringList>> \| Scripts to run
before building \|pre_run_scripts \| <<StringList,StringList>> \|
Scripts to run before running simulations \|pre_synth_scripts \|
<<StringList,StringList>> \| Scripts to run before backend synthesis
\|==============================

verilator ~~~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|cli_parser \| String \| Select CLI argument
parser. Set to ‘fusesoc’ to handle parameter sections like other
simulators. Set to ‘passthrough’ to send the arguments directly to the
verilated model. Default is ‘passthrough’ \|define_files \|
<<PathList,PathList>> \| Verilog include files containing \`define
directives to be converted to C #define directives in corresponding .h
files (deprecated) \|depend \| <<VlnvList,VlnvList>> \| Tool-specific
Dependencies \|include_files \| <<FileList,FileList>> \| Verilator
testbench C include files \|libs \| <<PathList,PathList>> \| External
libraries linked with the generated model \|source_type \| String \|
Testbench source code language (Legal values are systemC, C, CPP.
Default is C) \|src_files \| <<FileList,FileList>> \| Verilator
testbench C/cpp/sysC source files \|tb_toplevel \| <<FileList,FileList>>
\| Testbench top-level C/C++/SC file \|top_module \| String \| verilog
top-level module \|verilator_options \| <<StringList,StringList>> \|
Verilator build options \|==============================

verilog ~~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|file_type \| String \| Default file type of the
files in fileset \|include_files \| <<FileList,FileList>> \| Verilog
include files \|src_files \| <<FileList,FileList>> \| Verilog source
files for synthesis/simulation \|tb_include_files \|
<<FileList,FileList>> \| Testbench include files \|tb_private_src_files
\| <<FileList,FileList>> \| Verilog source files that are only used in
the core’s own testbench. Not visible to other cores \|tb_src_files \|
<<FileList,FileList>> \| Verilog source files that are only used in
simulation. Visible to other cores \|==============================

vhdl ~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|src_files \| <<PathList,PathList>> \| VHDL
source files for simulation and synthesis
\|==============================

vivado ~~~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|hw_device \| String \| FPGA device
identifier \|part \| String \| FPGA device part \|top_module \| String
\| RTL top-level module \|==============================

vpi ~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|include_files \| <<FileList,FileList>> \| C
include files for VPI library \|libs \| <<StringList,StringList>> \|
External libraries linked with the VPI library \|src_files \|
<<FileList,FileList>> \| C source files for VPI library
\|==============================

xsim ~~~~

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|depend \| <<VlnvList,VlnvList>> \|
Tool-specific Dependencies \|xsim_options \| <<StringList,StringList>>
\| Extra Xsim compile options \|==============================

provider ~~~~~~~~ The provider section gives information on where to
find the source code for the core. If the provider section is missing,
the core is assumed to be local, with the directory of the .core file as
the root directory.

[cols=“2,1,5”,options=“header”] \|============================== \|Name
\| Type \| Description \|name \| String \| The name option selects which
provider backend to use. All other provider options are specific to the
selected provider. Currently supported backends are github, git,
opencores, submodule and url. \|cachable \| boolean \| If the cachable
option is set to false, FuseSoc will unconditionally refetch the core
even if it is found in the cache. Default is true
\|==============================

Provider-specific options:

github ^^^^^^ \* *user :* Name of the github user or organisation.

-  *repo :* Name of the GIT repository.

-  *version :* Name of the GIT ref (i.e. commit SHA, branch or tag) to
   use

git ^^^ \* *repo :* URL of the GIT repository.

-  *version :* Name of the GIT ref (i.e. commit SHA, branch or tag) to
   use

opencores ^^^^^^^^^ \* *repo_name :* Name of the opencores project. Can
be found under Details on the project homepage.

-  *repo_root :* The sub directory in the repo that contains the files
   of interest. In most cases the value “trunk” is used to avoid pulling
   in tags and branches.

-  *revision :* The svn revision of the repository.

url ^^^ \* *url :* URL of the core file (or archive).

-  *filetype :* File type (zip, tar, simple).

Known issues
------------

. The configparser in python 2 doesn’t handle spaces before values in
multiline options. + .Illegal comment style ————– src_files = clkgen.v
#gpio.v fusesoc_top.v ————– + This is not legal in python 2, while: +
.Legal comment style ————– src_files = clkgen.v # gpio.v fusesoc_top.v
————– + is ok in python 2 and python 3. + . Spaces are not allowed
anywhere in the paths.
