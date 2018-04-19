vlib work
vlog some vlog_options -sv +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello +incdir+. -quiet -work work sv_file.sv
vlog some vlog_options +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello +incdir+. -quiet -work work vlog_file.v
vlog some vlog_options -v2k5 +define+vlogdefine_bool=1 +define+vlogdefine_int=42 +define+vlogdefine_str=hello +incdir+. -quiet -work work vlog05_file.v
vcom -quiet -work work vhdl_file.vhd
vlib libx
vcom -quiet -work libx vhdl_lfile
vcom -2008 -quiet -work work vhdl2008_file
