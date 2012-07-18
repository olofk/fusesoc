//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_cpu_registers.v                                         ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC Debug Interface.               ////
////  http://www.opencores.org/projects/DebugInterface/           ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////                                                              ////
////                                                              ////
////  All additional information is avaliable in the README.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2004 Authors                            ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
//
// CVS Revision History
//
// $Log: dbg_cpu_registers.v,v $
// Revision 1.6  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.5  2004/03/22 16:35:46  igorm
// Temp version before changing dbg interface.
//
// Revision 1.4  2004/01/25 14:04:18  mohor
// All flipflops are reset.
//
// Revision 1.3  2004/01/22 10:16:08  mohor
// cpu_stall_o activated as soon as bp occurs.
//
// Revision 1.2  2004/01/17 17:01:14  mohor
// Almost finished.
//
// Revision 1.1  2004/01/16 14:53:33  mohor
// *** empty log message ***
//
//
//

// synopsys translate_off
`include "timescale.v"
// synopsys translate_on
`include "dbg_cpu_defines.v"

module dbg_cpu_registers  (
                            data_i, 
                            we_i, 
                            tck_i, 
                            bp_i, 
                            rst_i,
                            cpu_clk_i, 
                            ctrl_reg_o,
                            cpu_stall_o, 
                            cpu_rst_o 
                          );


input  [`DBG_CPU_CTRL_LEN -1:0] data_i;
input                   we_i;
input                   tck_i;
input                   bp_i;
input                   rst_i;
input                   cpu_clk_i;

output [`DBG_CPU_CTRL_LEN -1:0]ctrl_reg_o;
output                  cpu_stall_o;
output                  cpu_rst_o;

reg                     cpu_reset;
wire             [2:1]  cpu_op_out;

reg                     stall_bp, stall_bp_csff, stall_bp_tck;
reg                     stall_reg, stall_reg_csff, stall_reg_cpu;
reg                     cpu_reset_csff;
reg                     cpu_rst_o;



// Breakpoint is latched and synchronized. Stall is set and latched.
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if(rst_i)
    stall_bp <=  1'b0;
  else if(bp_i)
    stall_bp <=  1'b1;
  else if(stall_reg_cpu)
    stall_bp <=  1'b0;
end


// Synchronizing
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      stall_bp_csff <=  1'b0;
      stall_bp_tck  <=  1'b0;
    end
  else
    begin
      stall_bp_csff <=  stall_bp;
      stall_bp_tck  <=  stall_bp_csff;
    end
end


always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      stall_reg_csff <=  1'b0;
      stall_reg_cpu  <=  1'b0;
    end
  else
    begin
      stall_reg_csff <=  stall_reg;
      stall_reg_cpu  <=  stall_reg_csff;
    end
end


assign cpu_stall_o = bp_i | stall_bp | stall_reg_cpu;


// Writing data to the control registers (stall)
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    stall_reg <=  1'b0;
  else if (stall_bp_tck)
    stall_reg <=  1'b1;
  else if (we_i)
    stall_reg <=  data_i[0];
end


// Writing data to the control registers (reset)
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    cpu_reset  <=  1'b0;
  else if(we_i)
    cpu_reset  <=  data_i[1];
end


// Synchronizing signals from registers
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      cpu_reset_csff      <=  1'b0; 
      cpu_rst_o           <=  1'b0; 
    end
  else
    begin
      cpu_reset_csff      <=  cpu_reset;
      cpu_rst_o           <=  cpu_reset_csff;
    end
end



// Value for read back
assign ctrl_reg_o = {cpu_reset, stall_reg};


endmodule

