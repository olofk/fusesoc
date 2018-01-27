vsim -pli elf-loader_0 orpsoc_tb +plusarg_bool=1 +plusarg_int=42 +plusarg_str=hello -gvlogparam_bool=1 -gvlogparam_int=42 -gvlogparam_str=hello
run -all
