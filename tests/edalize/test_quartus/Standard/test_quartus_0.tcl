project_new test_quartus_0 -overwrite
set_global_assignment -name FAMILY "Cyclone V"
set_global_assignment -name DEVICE 5CSXFC6D6F31C8ES
set_global_assignment -name TOP_LEVEL_ENTITY top_module
set_global_assignment -name VHDL_INPUT_VERSION VHDL_2008
set_parameter -name vlogparam_bool 1
set_parameter -name vlogparam_int 42
set_parameter -name vlogparam_str hello
set_global_assignment -name VERILOG_MACRO "vlogdefine_bool=1"
set_global_assignment -name VERILOG_MACRO "vlogdefine_int=42"
set_global_assignment -name VERILOG_MACRO "vlogdefine_str=hello"
set_global_assignment -name QIP_FILE qip_file.qip
set_global_assignment -name QIP_FILE qsys/qsys_file/qsys_file.qip
set_global_assignment -name SDC_FILE sdc_file
set_global_assignment -name SYSTEMVERILOG_FILE sv_file.sv
source tcl_file.tcl
set_global_assignment -name VERILOG_FILE vlog_file.v
set_global_assignment -name VERILOG_FILE vlog05_file.v
set_global_assignment -name VHDL_FILE vhdl_file.vhd
set_global_assignment -name VHDL_FILE -library libx vhdl_lfile
set_global_assignment -name VHDL_FILE vhdl2008_file
set_global_assignment -name SEARCH_PATH .
