# Auto-generated program tcl file

open_hw
connect_hw_server

set board ""

foreach  [get_hw_targets] {{
    puts "$target"
    current_hw_target $target
    open_hw_target
    if {{ [get_hw_devices] == "xc7a35t_0" }} {{
        set board [current_hw_target]
        break
    }}
    close_hw_target
}}


if {{ $board == "" }} {{
    puts "Did not find board"
    exit 1
}}

current_hw_device xc7a35t_0
set_property PROGRAM.FILE "" [current_hw_device]
program_hw_devices [current_hw_device]