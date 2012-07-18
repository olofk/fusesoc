//////////////////////////////////////////////////////////////////////
///                                                               //// 
/// Wishbone arbiter, burst-compatible                            ////
///                                                               ////
/// Simple arbiter, single master, dual slave, primarily for      ////
/// processor instruction bus, providing access to one main       ////
/// memory server and one ROM                                     ////
///                                                               ////
/// Julius Baxter, julius@opencores.org                           ////
///                                                               ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2009, 2010 Authors and OPENCORES.ORG           ////
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
`include "orpsoc-defines.v"
// One master, 2 slaves.
module arbiter_ibus
  (
   // instruction bus in
   // Wishbone Master interface
   wbm_adr_o,
   wbm_dat_o,
   wbm_sel_o,
   wbm_we_o,
   wbm_cyc_o,
   wbm_stb_o,
   wbm_cti_o,
   wbm_bte_o,
  
   wbm_dat_i,
   wbm_ack_i,
   wbm_err_i,
   wbm_rty_i,


   // Slave one
   // Wishbone Slave interface
   wbs0_adr_i,
   wbs0_dat_i,
   wbs0_sel_i,
   wbs0_we_i,
   wbs0_cyc_i,
   wbs0_stb_i,
   wbs0_cti_i,
   wbs0_bte_i,
  
   wbs0_dat_o,
   wbs0_ack_o,
   wbs0_err_o,
   wbs0_rty_o,

   // Slave two
   // Wishbone Slave interface
   wbs1_adr_i,
   wbs1_dat_i,
   wbs1_sel_i,
   wbs1_we_i,
   wbs1_cyc_i,
   wbs1_stb_i,
   wbs1_cti_i,
   wbs1_bte_i,
  
   wbs1_dat_o,
   wbs1_ack_o,
   wbs1_err_o,
   wbs1_rty_o,

   wb_clk,
   wb_rst
   );


   parameter wb_dat_width = 32;
   parameter wb_adr_width = 32;

   parameter wb_addr_match_width = 8;

   parameter slave0_adr = 8'hf0; // FLASH ROM
   parameter slave1_adr = 8'h00; // Main memory (SDRAM/FPGA SRAM)

`define WB_ARB_ADDR_MATCH_SEL wb_adr_width-1:wb_adr_width-wb_addr_match_width
   
   input wb_clk;
   input wb_rst;

   
   // WB Master
   input [wb_adr_width-1:0] wbm_adr_o;
   input [wb_dat_width-1:0] wbm_dat_o;
   input [3:0] 		    wbm_sel_o;   
   input 		    wbm_we_o;
   input 		    wbm_cyc_o;
   input 		    wbm_stb_o;
   input [2:0] 		    wbm_cti_o;
   input [1:0] 		    wbm_bte_o;
   output [wb_dat_width-1:0] wbm_dat_i;   
   output 		     wbm_ack_i;
   output 		     wbm_err_i;
   output 		     wbm_rty_i;   

   // WB Slave 0
   output [wb_adr_width-1:0] wbs0_adr_i;
   output [wb_dat_width-1:0] wbs0_dat_i;
   output [3:0] 	     wbs0_sel_i;
   output 		     wbs0_we_i;
   output 		     wbs0_cyc_i;
   output 		     wbs0_stb_i;
   output [2:0] 	     wbs0_cti_i;
   output [1:0] 	     wbs0_bte_i;
   input [wb_dat_width-1:0]  wbs0_dat_o;   
   input 		     wbs0_ack_o;
   input 		     wbs0_err_o;
   input 		     wbs0_rty_o;   

   // WB Slave 1
   output [wb_adr_width-1:0] wbs1_adr_i;
   output [wb_dat_width-1:0] wbs1_dat_i;
   output [3:0] 	     wbs1_sel_i;
   output 		     wbs1_we_i;
   output 		     wbs1_cyc_i;
   output 		     wbs1_stb_i;
   output [2:0] 	     wbs1_cti_i;
   output [1:0] 	     wbs1_bte_i;
   input [wb_dat_width-1:0]  wbs1_dat_o;   
   input 		     wbs1_ack_o;
   input 		     wbs1_err_o;
   input 		     wbs1_rty_o;   

   wire [1:0] 		     slave_sel; // One bit per slave

   reg 			     watchdog_err;
   
`ifdef ARBITER_IBUS_WATCHDOG
   reg [`ARBITER_IBUS_WATCHDOG_TIMER_WIDTH:0]  watchdog_timer;
   reg 			     wbm_stb_r; // Register strobe
   wire 		     wbm_stb_edge; // Detect its edge
   reg 			     wbm_stb_edge_r, wbm_ack_i_r; // Reg these, better timing

   always @(posedge wb_clk)
     wbm_stb_r <= wbm_stb_o;

   assign wbm_stb_edge = (wbm_stb_o & !wbm_stb_r);

   always @(posedge wb_clk)
     wbm_stb_edge_r <= wbm_stb_edge;
   
   always @(posedge wb_clk)
     wbm_ack_i_r <= wbm_ack_i;
   
   
   // Counter logic
   always @(posedge wb_clk)
     if (wb_rst) watchdog_timer <= 0;
     else if (wbm_ack_i_r) // When we see an ack, turn off timer
       watchdog_timer <= 0;
     else if (wbm_stb_edge_r) // New access means start timer again
       watchdog_timer <= 1;
     else if (|watchdog_timer) // Continue counting if counter > 0
       watchdog_timer <= watchdog_timer + 1;

   always @(posedge wb_clk) 
     watchdog_err <= (&watchdog_timer);
   
`else // !`ifdef ARBITER_IBUS_WATCHDOG
   
   always @(posedge wb_clk) 
     watchdog_err <= 0;

`endif // !`ifdef ARBITER_IBUS_WATCHDOG
   
   

`ifdef ARBITER_IBUS_REGISTERING
   
   // Master input registers
   reg [wb_adr_width-1:0]    wbm_adr_o_r;
   reg [wb_dat_width-1:0]    wbm_dat_o_r;
   reg [3:0] 		     wbm_sel_o_r;   
   reg 			     wbm_we_o_r;
   reg 			     wbm_cyc_o_r;
   reg 			     wbm_stb_o_r;
   reg [2:0] 		     wbm_cti_o_r;
   reg [1:0] 		     wbm_bte_o_r;
   // Slave output registers
   reg [wb_dat_width-1:0]    wbs0_dat_o_r;   
   reg 			     wbs0_ack_o_r;
   reg 			     wbs0_err_o_r;
   reg 			     wbs0_rty_o_r;
   reg [wb_dat_width-1:0]    wbs1_dat_o_r;   
   reg 			     wbs1_ack_o_r;
   reg 			     wbs1_err_o_r;
   reg 			     wbs1_rty_o_r;

   wire 		     wbm_ack_i_pre_reg;

   
   
   // Register master input signals
   always @(posedge wb_clk)
     begin
	wbm_adr_o_r <= wbm_adr_o;
	wbm_dat_o_r <= wbm_dat_o;
	wbm_sel_o_r <= wbm_sel_o;
	wbm_we_o_r <= wbm_we_o;
	wbm_cyc_o_r <= wbm_cyc_o;
	wbm_stb_o_r <= wbm_stb_o & !wbm_ack_i_pre_reg & !wbm_ack_i;//classic
	wbm_cti_o_r <= wbm_cti_o;
	wbm_bte_o_r <= wbm_bte_o;

	// Slave signals
	wbs0_dat_o_r <= wbs0_dat_o;
	wbs0_ack_o_r <= wbs0_ack_o;
	wbs0_err_o_r <= wbs0_err_o;
	wbs0_rty_o_r <= wbs0_rty_o;
	wbs1_dat_o_r <= wbs1_dat_o;
	wbs1_ack_o_r <= wbs1_ack_o;
	wbs1_err_o_r <= wbs1_err_o;
	wbs1_rty_o_r <= wbs1_rty_o;   
	
     end // always @ (posedge wb_clk)

   // Slave select
   assign slave_sel[0] = wbm_adr_o_r[`WB_ARB_ADDR_MATCH_SEL] ==
			 slave0_adr;

   assign slave_sel[1] = wbm_adr_o_r[`WB_ARB_ADDR_MATCH_SEL] ==
			 slave1_adr;

   // Slave out assigns
   assign wbs0_adr_i = wbm_adr_o_r;
   assign wbs0_dat_i = wbm_dat_o_r;
   assign wbs0_we_i = wbm_dat_o_r;
   assign wbs0_sel_i = wbm_sel_o_r;
   assign wbs0_cti_i = wbm_cti_o_r;
   assign wbs0_bte_i = wbm_bte_o_r;
   assign wbs0_cyc_i = wbm_cyc_o_r & slave_sel[0];
   assign wbs0_stb_i = wbm_stb_o_r & slave_sel[0];

   assign wbs1_adr_i = wbm_adr_o_r;
   assign wbs1_dat_i = wbm_dat_o_r;
   assign wbs1_we_i = wbm_dat_o_r;
   assign wbs1_sel_i = wbm_sel_o_r;
   assign wbs1_cti_i = wbm_cti_o_r;
   assign wbs1_bte_i = wbm_bte_o_r;
   assign wbs1_cyc_i = wbm_cyc_o_r & slave_sel[1];
   assign wbs1_stb_i = wbm_stb_o_r & slave_sel[1];

   // Master out assigns
   // Don't care about none selected...
   assign wbm_dat_i = slave_sel[1] ? wbs1_dat_o_r :
		      wbs0_dat_o_r ;
   
   assign wbm_ack_i = (slave_sel[0] & wbs0_ack_o_r) |
		      (slave_sel[1] & wbs1_ack_o_r)
     ;
   
   assign wbm_err_i = (slave_sel[0] & wbs0_err_o_r) |
		      (slave_sel[1] & wbs1_err_o_r) |
		      watchdog_err;
   
   assign wbm_rty_i = (slave_sel[0] & wbs0_rty_o_r) |
		      (slave_sel[1] & wbs1_rty_o_r);

   // Non-registered ack
   assign wbm_ack_i_pre_reg = (slave_sel[0] & wbs0_ack_o) |
			      (slave_sel[1] & wbs1_ack_o);
   
`else // !`ifdef ARBITER_IBUS_REGISTERING

   // Slave select
   assign slave_sel[0] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] ==
			 slave0_adr;

   assign slave_sel[1] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] ==
			 slave1_adr;

   // Slave out assigns
   assign wbs0_adr_i = wbm_adr_o;
   assign wbs0_dat_i = wbm_dat_o;
   assign wbs0_we_i  = wbm_we_o;
   assign wbs0_sel_i = wbm_sel_o;
   assign wbs0_cti_i = wbm_cti_o;
   assign wbs0_bte_i = wbm_bte_o;
   assign wbs0_cyc_i = wbm_cyc_o & slave_sel[0];
   assign wbs0_stb_i = wbm_stb_o & slave_sel[0];

   assign wbs1_adr_i = wbm_adr_o;
   assign wbs1_dat_i = wbm_dat_o;
   assign wbs1_we_i  = wbm_we_o;
   assign wbs1_sel_i = wbm_sel_o;
   assign wbs1_cti_i = wbm_cti_o;
   assign wbs1_bte_i = wbm_bte_o;
   assign wbs1_cyc_i = wbm_cyc_o & slave_sel[1];
   assign wbs1_stb_i = wbm_stb_o & slave_sel[1];

   // Master out assigns
   // Don't care about none selected...
   assign wbm_dat_i = slave_sel[1] ? wbs1_dat_o :
		      wbs0_dat_o ;
   
   assign wbm_ack_i = (slave_sel[0] & wbs0_ack_o) |
		      (slave_sel[1] & wbs1_ack_o);
   
   
   assign wbm_err_i = (slave_sel[0] & wbs0_err_o) |
		      (slave_sel[1] & wbs1_err_o) |
		      watchdog_err;
   
   assign wbm_rty_i = (slave_sel[0] & wbs0_rty_o) |
		      (slave_sel[1] & wbs1_rty_o);
   

`endif
endmodule // arbiter_ibus

