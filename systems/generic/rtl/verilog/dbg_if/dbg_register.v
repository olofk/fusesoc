//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_register.v                                              ////
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
// $Log: dbg_register.v,v $
// Revision 1.10  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.9  2004/01/25 14:04:18  mohor
// All flipflops are reset.
//
// Revision 1.8  2004/01/16 14:53:33  mohor
// *** empty log message ***
//
//
//

// synopsys translate_off
`include "timescale.v"
// synopsys translate_on

module dbg_register (
                      data_in, 
                      data_out, 
                      write, 
                      clk, 
                      reset
                    );


parameter WIDTH = 8; // default parameter of the register width
parameter RESET_VALUE = 0;


input   [WIDTH-1:0] data_in;
input               write;
input               clk;
input               reset;

output  [WIDTH-1:0] data_out;
reg     [WIDTH-1:0] data_out;



always @ (posedge clk or posedge reset)
begin
  if(reset)
    data_out[WIDTH-1:0] <=  RESET_VALUE;
  else if(write)
    data_out[WIDTH-1:0] <=  data_in[WIDTH-1:0];
end


endmodule   // Register

