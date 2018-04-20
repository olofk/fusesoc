# Auto-generated project tcl file

create_project -part "xc7a35tcsg324-1" test_vivado_0

set_property "simulator_language" "Mixed" [current_project]

source tcl_file.tcl

read_ip xci_file.xci
upgrade_ip [get_ips]
generate_target all [get_ips]


read_verilog vlog_file.v
read_verilog vlog05_file.v
read_verilog -sv sv_file.sv
read_vhdl vhdl_file.vhd
read_vhdl -library libx vhdl_lfile
read_vhdl -vhdl2008 vhdl2008_file

set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello} [get_filesets sources_1]
set_property verilog_define "vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello" [get_filesets sources_1]


set_property include_dirs [list .] [get_filesets sources_1]



set_param project.enableVHDL2008 1
set_property top top_module [current_fileset]
set_property source_mgmt_mode None [current_project]


# By default create_project creates the synth_1 and impl_1 runs.
# To explicitly create customized runs, uncomment the code below.
#regexp -- {Vivado v([0-9]{4})\.[0-9]} [version] -> year
#create_run synth_1 -quiet -flow "Vivado Synthesis $year" -strategy "Vivado Synthesis Defaults"
#create_run impl_1 -quiet -flow "Vivado Implementation $year" -strategy "Vivado Implementation Defaults" -parent_run synth_1
#current_run [get_runs synth_1]

launch_runs impl_1
wait_on_run impl_1
open_run impl_1
write_bitstream test_vivado_0.bit
