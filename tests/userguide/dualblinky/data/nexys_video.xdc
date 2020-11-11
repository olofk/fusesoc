## Clock Signal
set_property -dict { PACKAGE_PIN R4    IOSTANDARD LVCMOS33 } [get_ports { clk }]; #IO_L13P_T2_MRCC_34 Sch=sysclk
create_clock -add -name sys_clk_pin -period 10.00 -waveform {0 5} [get_ports clk]

## LED
set_property -dict { PACKAGE_PIN T14   IOSTANDARD LVCMOS25 } [get_ports { q[0] }]; #IO_L15P_T2_DQS_13 Sch=led[0]
set_property -dict { PACKAGE_PIN T15   IOSTANDARD LVCMOS25 } [get_ports { q[1] }]; #IO_L15N_T2_DQS_13 Sch=led[1]

## Buttons
set_property -dict { PACKAGE_PIN G4  IOSTANDARD LVCMOS15 } [get_ports { rst_n }]; #IO_L12N_T1_MRCC_35 Sch=cpu_resetn
