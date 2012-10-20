//////////////////////////////////////////////////////////////////////
///                                                               //// 
/// Wishbone arbiter, burst-compatible                            ////
///                                                               ////
/// Simple arbiter, multi-master, multi-slave with default slave  ////
/// for chaining with peripheral arbiter                          ////
///                                                               ////
/// Olof Kindgren, olof@opencores.org                             ////
///                                                               ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2012 Authors and OPENCORES.ORG                 ////
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

module wb_arbiter
  (
   input 		      wb_clk,
   input 		      wb_rst,

   // Wishbone Master Interface
   input [num_masters*aw-1:0] wbm_adr_i,
   input [num_masters*dw-1:0] wbm_dat_i,
   input [num_masters*4-1:0]  wbm_sel_i,
   input [num_masters-1:0]    wbm_we_i,
   input [num_masters-1:0]    wbm_cyc_i,
   input [num_masters-1:0]    wbm_stb_i,
   input [num_masters*3-1:0]  wbm_cti_i,
   input [num_masters*2-1:0]  wbm_bte_i,
   output [num_masters*dw-1:0] wbm_sdt_o,
   output [num_masters-1:0]   wbm_ack_o,
   output [num_masters-1:0]   wbm_err_o,
   output [num_masters-1:0]   wbm_rty_o, 

   // Wishbone Slave interface
   output [aw-1:0] 	      wbs_adr_o,
   output [dw-1:0] 	      wbs_dat_o,
   output [3:0] 	      wbs_sel_o, 
   output 		      wbs_we_o,
   output 		      wbs_cyc_o,
   output 		      wbs_stb_o,
   output [2:0] 	      wbs_cti_o,
   output [1:0] 	      wbs_bte_o,
   input [dw-1:0] 	      wbs_sdt_i,
   input 		      wbs_ack_i,
   input 		      wbs_err_i,
   input 		      wbs_rty_i);


///////////////////////////////////////////////////////////////////////////////
// Parameters
///////////////////////////////////////////////////////////////////////////////

   parameter dw = 32;
   parameter aw = 32;

   parameter num_masters = 2;

   // Master select (MUX controls)
   reg [1:0]                master_sel;

   reg [1:0] i;
   
   always @(wbm_cyc_i) begin
      master_sel = 0;
      
      for(i=0;i<num_masters;i=i+1) begin : master_sel_loop
	 if(wbm_cyc_i[i] == 1'b1)
	   master_sel = i;
      end
   end
   
   //Mux active master
   assign wbs_adr_o = wbm_adr_i[master_sel*aw+:aw];
   assign wbs_dat_o = wbm_dat_i[master_sel*dw+:dw];
   assign wbs_sel_o = wbm_sel_i[master_sel*4+:4];
   assign wbs_we_o  = wbm_we_i [master_sel];
   assign wbs_cyc_o = wbm_cyc_i[master_sel];
   assign wbs_stb_o = wbm_stb_i[master_sel];
   assign wbs_cti_o = wbm_cti_i[master_sel*3+:3];
   assign wbs_bte_o = wbm_bte_i[master_sel*2+:2];

   assign wbm_sdt_o = {num_masters{wbs_sdt_i}};
   assign wbm_ack_o = wbs_ack_i << master_sel;
   assign wbm_err_o = wbs_err_i << master_sel;
   assign wbm_rty_o = wbs_rty_i << master_sel;
   
endmodule // wb_arbiter

