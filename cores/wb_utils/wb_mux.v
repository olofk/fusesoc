//////////////////////////////////////////////////////////////////////
///                                                               //// 
/// Wishbone multiplexer, burst-compatible                        ////
///                                                               ////
/// Simple mux with an arbitrary number of slaves.                ////
///                                                               ////
/// The active slave is selected by asserting the corresponding   ////
/// slave_sel_i bit. If several slave_sel signals are asserted,   ////
/// the slave with the lowest number will be selected. If no bits ////
/// are asserted, the last slave is selected to enable chaining   ////
///  with other arbiters                                          ////
///                                                               ////
/// Olof Kindgren, olof@opencores.org                             ////
///                                                               ////
/// Todo:                                                         ////
/// Registered master/slave connections                           ////
/// Rewrite with System Verilog 2D arrays when tools support them ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2011 Authors and OPENCORES.ORG                 ////
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

module wb_mux
  #(parameter watchdog = 0, //Set to non-zero to enable watchdog
    parameter watchdog_timer_width = 12,
    parameter dw = 32,
    parameter aw = 32,
    parameter num_slaves = 2)

   (input                      wb_clk,
    input                      wb_rst,

    input     [num_slaves-1:0] slave_sel_i,
    // Master Interface
    input             [aw-1:0] wbm_adr_i,
    input             [dw-1:0] wbm_dat_i,
    input                [3:0] wbm_sel_i,
    input                      wbm_we_i,
    input                      wbm_cyc_i,
    input                      wbm_stb_i,
    input                [2:0] wbm_cti_i,
    input                [1:0] wbm_bte_i,
    output            [dw-1:0] wbm_sdt_o,
    output                     wbm_ack_o,
    output                     wbm_err_o,
    output                     wbm_rty_o,   
    // Wishbone Slave interface
    output            [aw-1:0] wbs_adr_o,
    output            [dw-1:0] wbs_dat_o,
    output               [3:0] wbs_sel_o,  
    output                     wbs_we_o,
    output    [num_slaves-1:0] wbs_cyc_o,
    output    [num_slaves-1:0] wbs_stb_o,
    output               [2:0] wbs_cti_o,
    output               [1:0] wbs_bte_o,
    input  [dw*num_slaves-1:0] wbs_sdt_i,
    input     [num_slaves-1:0] wbs_ack_i,
    input     [num_slaves-1:0] wbs_err_i,
    input     [num_slaves-1:0] wbs_rty_i);
      
///////////////////////////////////////////////////////////////////////////////
// Watchdog timer
///////////////////////////////////////////////////////////////////////////////
reg watchdog_err;

generate
   if (watchdog == 1) begin : gen_watchdog_timer
     
      reg [watchdog_timer_width:0] watchdog_timer;
      reg                          wbm_stb_r; // Register strobe

      always @(posedge wb_clk)
        wbm_stb_r <= wbm_stb_i;

      wire                         wbm_stb_edge = (wbm_stb_i & !wbm_stb_r); //Edge detect
   
      // Counter logic
      always @(posedge wb_clk)
        if (wb_rst) watchdog_timer <= 0;
        else if (wbm_ack_o) // When we see an ack, turn off timer
          watchdog_timer <= 0;
        else if (wbm_stb_edge) // New access means start timer again
          watchdog_timer <= 1;
        else if (|watchdog_timer) // Continue counting if counter > 0
          watchdog_timer <= watchdog_timer + 1'b0;

      always @(posedge wb_clk) 
        watchdog_err <= (&watchdog_timer);

   end else begin : no_watchdog_timer

      always @(posedge wb_clk)
        watchdog_err <= 0;

   end
endgenerate

///////////////////////////////////////////////////////////////////////////////
// Master/slave connection
///////////////////////////////////////////////////////////////////////////////


   assign wbs_adr_o = wbm_adr_i;
   assign wbs_dat_o = wbm_dat_i;
   assign wbs_sel_o = wbm_sel_i;
   assign wbs_we_o  = wbm_we_i; 

   //FIXME: Do we need to cut off both cyc and stb?
   assign wbs_cyc_o = {num_slaves{wbm_cyc_i}} & slave_sel_i;
   assign wbs_stb_o = {num_slaves{wbm_stb_i}} & slave_sel_i;

   assign wbs_cti_o = wbm_cti_i;
   assign wbs_bte_o = wbm_bte_i;

   wire [num_slaves-1:0] dat_arr[0:dw-1];

   integer i;
   reg [1:0] slave_sel;
   
   always @(slave_sel_i) begin
      slave_sel = num_slaves-2'd1;
      
      for(i=0;i<num_slaves;i=i+1) begin : slave_sel_loop
	 if(slave_sel_i[i] == 1) slave_sel = i;
      end
   end

   assign wbm_sdt_o = wbs_sdt_i[slave_sel*32+:32];
   assign wbm_ack_o = wbs_ack_i[slave_sel];
   assign wbm_err_o = wbs_err_i[slave_sel] | watchdog_err;
   assign wbm_rty_o = wbs_rty_i[slave_sel];

endmodule // wb_mux
