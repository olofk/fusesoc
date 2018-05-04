# Auto-generated project tcl file

create_project test_vivado_0

set_property part xc7a35tcsg324-1 [current_project]
#Default since Vivado 2016.1
set_param project.enableVHDL2008 1
set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello } [get_filesets sources_1]
set_property verilog_define {vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello } [get_filesets sources_1]
read_verilog -sv sv_file.sv
source tcl_file.tcl
read_verilog vlog_file.v
read_verilog vlog05_file.v
read_vhdl vhdl_file.vhd
read_vhdl -library libx vhdl_lfile
read_vhdl -vhdl2008 vhdl2008_file
read_ip xci_file.xci
read_xdc xdc_file.xdc

set_property include_dirs [list .] [get_filesets sources_1]
set_property top top_module [current_fileset]
set_property source_mgmt_mode None [current_project]
upgrade_ip [get_ips]
generate_target all [get_ips]