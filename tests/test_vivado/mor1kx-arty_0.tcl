# Auto-generated project tcl file

create_project -part "xc7a35tcsg324-1" mor1kx-arty_0

set_property "simulator_language" "Mixed" [current_project]

source ../../../cores/misc/tcl_file.tcl

read_ip ../../../cores/misc/xci_file.xci
upgrade_ip [get_ips]
generate_target all [get_ips]


read_verilog ../../../cores/misc/vlog_file.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_branch_prediction.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_bus_if_avalon.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_bus_if_wb32.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cache_lru.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cfgrs.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cpu_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cpu_espresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cpu_prontoespresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_cpu.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_ctrl_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_ctrl_espresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_ctrl_prontoespresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_dcache.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_decode_execute_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_decode.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_dmmu.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_execute_alu.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_execute_ctrl_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_fetch_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_fetch_espresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_fetch_prontoespresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_fetch_tcm_prontoespresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_icache.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_immu.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_lsu_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_lsu_espresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_pic.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_rf_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_rf_espresso.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_simple_dpram_sclk.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_store_buffer.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_ticktimer.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_true_dpram_sclk.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_wb_mux_cappuccino.v
read_verilog ../../../cache/mor1kx_3.1/rtl/verilog/mor1kx_wb_mux_espresso.v
read_verilog ../../../cores/mor1kx-arty/rtl/verilog/mor1kx_arty.sv
read_verilog -sv ../../../cores/misc/sv_file.sv
read_vhdl ../../../cores/misc/vhdl_file.vhd
read_vhdl -library libx ../../../cores/misc/vhdl_lib_file.vhd
read_vhdl -vhdl2008 ../../../cores/misc/vhdl2008_file.vhd

set_property generic {vlogparam_bool=1 vlogparam_int=42 vlogparam_str=hello} [get_filesets sources_1]
set_property verilog_define "vlogdefine_bool=1 vlogdefine_int=42 vlogdefine_str=hello" [get_filesets sources_1]


set_property include_dirs [list ../../../cache/mor1kx_3.1/rtl/verilog] [get_filesets sources_1]

read_xdc ../../../cores/misc/xdc_file

set_param project.enableVHDL2008 1
set_property top mor1kx_arty_top [current_fileset]

# By default create_project creates the synth_1 and impl_1 runs.
# To explicitly create customized runs, uncomment the code below.
#regexp -- {Vivado v([0-9]{4})\.[0-9]} [version] -> year
#create_run synth_1 -quiet -flow "Vivado Synthesis $year" -strategy "Vivado Synthesis Defaults"
#create_run impl_1 -quiet -flow "Vivado Implementation $year" -strategy "Vivado Implementation Defaults" -parent_run synth_1
#current_run [get_runs synth_1]

launch_runs impl_1
wait_on_run impl_1
open_run impl_1
write_bitstream mor1kx-arty_0.bit
