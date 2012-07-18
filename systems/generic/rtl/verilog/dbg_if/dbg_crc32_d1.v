//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_crc32_d1.v                                              ////
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
// File:  CRC32_D1.v                             
// Date:  Thu Nov 27 13:56:49 2003                                                      
//                                                                     
// Copyright (C) 1999-2003 Easics NV.                 
// This source file may be used and distributed without restriction    
// provided that this copyright statement is not removed from the file 
// and that any derivative work contains the original copyright notice
// and the associated disclaimer.
//
// THIS SOURCE FILE IS PROVIDED "AS IS" AND WITHOUT ANY EXPRESS
// OR IMPLIED WARRANTIES, INCLUDING, WITHOUT LIMITATION, THE IMPLIED
// WARRANTIES OF MERCHANTIBILITY AND FITNESS FOR A PARTICULAR PURPOSE.
//
// Purpose: Verilog module containing a synthesizable CRC function
//   * polynomial: (0 1 2 4 5 7 8 10 11 12 16 22 23 26 32)
//   * data width: 1
//                                                                     
// Info: janz@easics.be (Jan Zegers)                           
//       http://www.easics.com                                  
///////////////////////////////////////////////////////////////////////
//
// CVS Revision History
//
// $Log: dbg_crc32_d1.v,v $
// Revision 1.3  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.2  2003/12/23 15:26:26  mohor
// Small fix.
//
// Revision 1.1  2003/12/23 15:09:04  mohor
// New directory structure. New version of the debug interface.
//
//
//
//

// synopsys translate_off
`include "timescale.v"
// synopsys translate_on

module dbg_crc32_d1 (data, enable, shift, rst, sync_rst, crc_out, clk, crc_match);

input         data;
input         enable;
input         shift;
input         rst;
input         sync_rst;
input         clk;


output        crc_out;
output        crc_match;

reg    [31:0] crc;

wire   [31:0] new_crc;

 
assign new_crc[0] = data          ^ crc[31];
assign new_crc[1] = data          ^ crc[0]  ^ crc[31];
assign new_crc[2] = data          ^ crc[1]  ^ crc[31];
assign new_crc[3] = crc[2];
assign new_crc[4] = data          ^ crc[3]  ^ crc[31];
assign new_crc[5] = data          ^ crc[4]  ^ crc[31];
assign new_crc[6] = crc[5];
assign new_crc[7] = data          ^ crc[6]  ^ crc[31];
assign new_crc[8] = data          ^ crc[7]  ^ crc[31];
assign new_crc[9] = crc[8];
assign new_crc[10] = data         ^ crc[9]  ^ crc[31];
assign new_crc[11] = data         ^ crc[10] ^ crc[31];
assign new_crc[12] = data         ^ crc[11] ^ crc[31];
assign new_crc[13] = crc[12];
assign new_crc[14] = crc[13];
assign new_crc[15] = crc[14];
assign new_crc[16] = data         ^ crc[15] ^ crc[31];
assign new_crc[17] = crc[16];
assign new_crc[18] = crc[17];
assign new_crc[19] = crc[18];
assign new_crc[20] = crc[19];
assign new_crc[21] = crc[20];
assign new_crc[22] = data         ^ crc[21] ^ crc[31];
assign new_crc[23] = data         ^ crc[22] ^ crc[31];
assign new_crc[24] = crc[23];
assign new_crc[25] = crc[24];
assign new_crc[26] = data         ^ crc[25] ^ crc[31];
assign new_crc[27] = crc[26];
assign new_crc[28] = crc[27];
assign new_crc[29] = crc[28];
assign new_crc[30] = crc[29];
assign new_crc[31] = crc[30];


always @ (posedge clk or posedge rst)
begin
  if(rst)
    crc[31:0] <=  32'hffffffff;
  else if(sync_rst)
    crc[31:0] <=  32'hffffffff;
  else if(enable)
    crc[31:0] <=  new_crc;
  else if (shift)
    crc[31:0] <=  {crc[30:0], 1'b0};
end


assign crc_match = (crc == 32'h0);
assign crc_out = crc[31];

endmodule
