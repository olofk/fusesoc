//////////////////////////////////////////////////////////////////////
//
// clkgen
//
// Handles clock and reset generation for rest of design
//
//
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
//
// A simple implementation for the main generic ORPSoC simulations
//

`include "timescale.v"
`include "orpsoc-defines.v"

module clkgen
  (
   // Main clocks in, depending on board
   clk_pad_i,

   // Input reset - through a buffer, asynchronous
   async_rst_o,
   // Wishbone clock and reset out  
   wb_clk_o,
   wb_rst_o,

   // JTAG clock
`ifdef JTAG_DEBUG
   tck_pad_i,
   dbg_tck_o,
`endif      

   // Asynchronous, active low reset in
   rst_n_pad_i
   
   );

   input clk_pad_i;
   
   output async_rst_o;
   
   output wb_rst_o;
   output wb_clk_o;

`ifdef JTAG_DEBUG
   input  tck_pad_i;
   output dbg_tck_o;
`endif      
   
   // Asynchronous, active low reset (pushbutton, typically)
   input  rst_n_pad_i;
   
   // First, deal with the asychronous reset
   wire   async_rst_n;

   // An input buffer is usually instantiated here
   assign async_rst_n = rst_n_pad_i;
   
   // Everyone likes active-high reset signals...
   assign async_rst_o = ~async_rst_n;
   
`ifdef JTAG_DEBUG
   assign dbg_tck_o = tck_pad_i;
`endif

   //
   // Declare synchronous reset wires here
   //
   
   // An active-low synchronous reset signal (usually a PLL lock signal)
   wire   sync_rst_n;
   assign sync_rst_n  = async_rst_n; // Pretend it's somehow synchronous now


   // Here we just assign "board" clock (really test) to wishbone clock
   assign wb_clk_o = clk_pad_i;
   
   //
   // Reset generation
   //
   //

   // Reset generation for wishbone
   reg [15:0] 	   wb_rst_shr;
   always @(posedge wb_clk_o or posedge async_rst_o)
     if (async_rst_o)
       wb_rst_shr <= 16'hffff;
     else
       wb_rst_shr <= {wb_rst_shr[14:0], ~(sync_rst_n)};
   
   assign wb_rst_o = wb_rst_shr[15];
   
endmodule // clkgen
