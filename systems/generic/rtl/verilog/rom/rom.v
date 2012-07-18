//////////////////////////////////////////////////////////////////////
////                                                              ////
////  ROM                                                         ////
////                                                              ////
////  Author(s):                                                  ////
////      - Michael Unneback (unneback@opencores.org)             ////
////      - Julius Baxter    (julius@opencores.org)               ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2009 Authors                                   ////
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
//`define B3_BURST
`define NONBLOCK_ASSIGN <= #1
module rom
  ( wb_adr_i, wb_stb_i, wb_cyc_i, wb_cti_i, wb_bte_i, 
    wb_dat_o, wb_ack_o, wb_clk, wb_rst);

   parameter addr_width = 5;
   
   input [(addr_width+2)-1:2]       wb_adr_i;
   input 			    wb_stb_i;
   input 			    wb_cyc_i;
   input [2:0] 			    wb_cti_i;
   input [1:0] 			    wb_bte_i;
   output reg [31:0] 		    wb_dat_o;
   output reg 			    wb_ack_o;
   input 			    wb_clk;
   input 			    wb_rst;
   
`ifdef B3_BURST
   reg [addr_width-1:0] 	    adr;
   reg 				    wb_stb_i_r;
   wire 			    new_access;
   reg 				    new_access_r;   
   wire 			    burst;
   reg 				    burst_r;
   wire 			    new_burst;   
   
`endif
   
   always @ (posedge wb_clk or posedge wb_rst)
     if (wb_rst)
       wb_dat_o `NONBLOCK_ASSIGN 32'h15000000;
     else
`ifdef B3_BURST
       case (adr)
`else       
	 case (wb_adr_i)
`endif	 
`include "bootrom.v"
	   /*	 
	    // Zero r0 and jump to 0x00000100
	    0 : wb_dat_o <= 32'h18000000;
	    1 : wb_dat_o <= 32'hA8200000;
	    2 : wb_dat_o <= 32'hA8C00100;
	    3 : wb_dat_o <= 32'h44003000;
	    4 : wb_dat_o <= 32'h15000000;
	    */
	   default:
	     wb_dat_o `NONBLOCK_ASSIGN 32'h00000000;
	     
	 endcase // case (wb_adr_i)
	 
`ifdef B3_BURST
	 
   always @(posedge wb_clk)
     wb_stb_i_r `NONBLOCK_ASSIGN wb_stb_i;

   assign new_access = (wb_stb_i & !wb_stb_i_r);

   always @(posedge wb_clk)
     new_access_r <= new_access;
      
   always @(posedge wb_clk)
     burst_r `NONBLOCK_ASSIGN burst;
   
   assign new_burst = (burst & !burst_r);
   
   always @(posedge wb_clk)
     if (wb_rst)
       adr `NONBLOCK_ASSIGN 0;
     else if (new_access)
       // New access, register address, ack a cycle later
       adr `NONBLOCK_ASSIGN wb_adr_i[(addr_width+2)-1:2];
     else if (burst)
       begin
	  if (wb_cti_i == 3'b010)
	    case (wb_bte_i)
	      2'b00: adr `NONBLOCK_ASSIGN adr + 1;
	      2'b01: adr[1:0] `NONBLOCK_ASSIGN adr[1:0] + 1;
	      2'b10: adr[2:0] `NONBLOCK_ASSIGN adr[2:0] + 1;
	      2'b11: adr[3:0] `NONBLOCK_ASSIGN adr[3:0] + 1;
	    endcase // case (wb_bte_i)
	  else
	    adr `NONBLOCK_ASSIGN wb_adr_i[(addr_width+2)-1:2];
       end // if (burst)
   
   
   always @(posedge wb_clk)
     if (wb_rst)
       wb_ack_o `NONBLOCK_ASSIGN 0;
     else if (wb_ack_o & (!burst | (wb_cti_i == 3'b111)))
       wb_ack_o `NONBLOCK_ASSIGN 0;
     else if (wb_stb_i & ((!burst & !new_access & new_access_r) | (burst & burst_r)))
       wb_ack_o `NONBLOCK_ASSIGN 1;
     else
       wb_ack_o `NONBLOCK_ASSIGN 0;

   
   assign burst = wb_cyc_i & (!(wb_cti_i == 3'b000)) & (!(wb_cti_i == 3'b111));
   
`else // !`ifdef B3_BURST
   
   always @ (posedge wb_clk or posedge wb_rst)
     if (wb_rst)
       wb_ack_o `NONBLOCK_ASSIGN 1'b0;
     else
       wb_ack_o `NONBLOCK_ASSIGN wb_stb_i & wb_cyc_i & !wb_ack_o;
   
`endif // !`ifdef B3_BURST
   
endmodule 
