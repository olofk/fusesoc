//////////////////////////////////////////////////////////////////////
///                                                               //// 
/// Wishbone arbiter, burst-compatible                            ////
///                                                               ////
/// Simple arbiter, multi-master, multi-slave with default slave  ////
/// for chaining with peripheral arbiter                          ////
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
// 2 Masters, a few slaves
module arbiter_dbus
  (
   // or1200 data master
   // Wishbone Master interface
   wbm0_adr_o,
   wbm0_dat_o,
   wbm0_sel_o,
   wbm0_we_o,
   wbm0_cyc_o,
   wbm0_stb_o,
   wbm0_cti_o,
   wbm0_bte_o,
  
   wbm0_dat_i,
   wbm0_ack_i,
   wbm0_err_i,
   wbm0_rty_i,

   // or1200 debug master
   // Wishbone Master interface
   wbm1_adr_o,
   wbm1_dat_o,
   wbm1_sel_o,
   wbm1_we_o,
   wbm1_cyc_o,
   wbm1_stb_o,
   wbm1_cti_o,
   wbm1_bte_o,
  
   wbm1_dat_i,
   wbm1_ack_i,
   wbm1_err_i,
   wbm1_rty_i,

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

   /*
   // Slave three
   // Wishbone Slave interface
   wbs2_adr_i,
   wbs2_dat_i,
   wbs2_sel_i,		    
   wbs2_we_i,
   wbs2_cyc_i,
   wbs2_stb_i,
   wbs2_cti_i,
   wbs2_bte_i,
  
   wbs2_dat_o,
   wbs2_ack_o,
   wbs2_err_o,
   wbs2_rty_o,

   // Slave four
   // Wishbone Slave interface
   wbs3_adr_i,
   wbs3_dat_i,
   wbs3_sel_i,		    
   wbs3_we_i,
   wbs3_cyc_i,
   wbs3_stb_i,
   wbs3_cti_i,
   wbs3_bte_i,
  
   wbs3_dat_o,
   wbs3_ack_o,
   wbs3_err_o,
   wbs3_rty_o,

   // Slave five
   // Wishbone Slave interface
   wbs4_adr_i,
   wbs4_dat_i,
   wbs4_sel_i,		    
   wbs4_we_i,
   wbs4_cyc_i,
   wbs4_stb_i,
   wbs4_cti_i,
   wbs4_bte_i,
  
   wbs4_dat_o,
   wbs4_ack_o,
   wbs4_err_o,
   wbs4_rty_o,

    // Slave six
    // Wishbone Slave interface
    wbs5_adr_i,
    wbs5_dat_i,
    wbs5_sel_i,		    
    wbs5_we_i,
    wbs5_cyc_i,
    wbs5_stb_i,
    wbs5_cti_i,
    wbs5_bte_i,
  
    wbs5_dat_o,
    wbs5_ack_o,
    wbs5_err_o,
    wbs5_rty_o,

    // Slave seven
    // Wishbone Slave interface
    wbs6_adr_i,
    wbs6_dat_i,
    wbs6_sel_i,		    
    wbs6_we_i,
    wbs6_cyc_i,
    wbs6_stb_i,
    wbs6_cti_i,
    wbs6_bte_i,
  
    wbs6_dat_o,
    wbs6_ack_o,
    wbs6_err_o,
    wbs6_rty_o,

    // Slave eight
    // Wishbone Slave interface
    wbs7_adr_i,
    wbs7_dat_i,
    wbs7_sel_i,		    
    wbs7_we_i,
    wbs7_cyc_i,
    wbs7_stb_i,
    wbs7_cti_i,
    wbs7_bte_i,
  
    wbs7_dat_o,
    wbs7_ack_o,
    wbs7_err_o,
    wbs7_rty_o,

    // Slave nine
    // Wishbone Slave interface
    wbs8_adr_i,
    wbs8_dat_i,
    wbs8_sel_i,		    
    wbs8_we_i,
    wbs8_cyc_i,
    wbs8_stb_i,
    wbs8_cti_i,
    wbs8_bte_i,
  
    wbs8_dat_o,
    wbs8_ack_o,
    wbs8_err_o,
    wbs8_rty_o,

    // Slave ten
    // Wishbone Slave interface
    wbs9_adr_i,
    wbs9_dat_i,
    wbs9_sel_i,		    
    wbs9_we_i,
    wbs9_cyc_i,
    wbs9_stb_i,
    wbs9_cti_i,
    wbs9_bte_i,
  
    wbs9_dat_o,
    wbs9_ack_o,
    wbs9_err_o,
    wbs9_rty_o,

    // Slave eleven
    // Wishbone Slave interface
    wbs10_adr_i,
    wbs10_dat_i,
    wbs10_sel_i,		    
    wbs10_we_i,
    wbs10_cyc_i,
    wbs10_stb_i,
    wbs10_cti_i,
    wbs10_bte_i,
  
    wbs10_dat_o,
    wbs10_ack_o,
    wbs10_err_o,
    wbs10_rty_o,

    // Slave twelve
    // Wishbone Slave interface
    wbs11_adr_i,
    wbs11_dat_i,
    wbs11_sel_i,		    
    wbs11_we_i,
    wbs11_cyc_i,
    wbs11_stb_i,
    wbs11_cti_i,
    wbs11_bte_i,
  
    wbs11_dat_o,
    wbs11_ack_o,
    wbs11_err_o,
    wbs11_rty_o,

    // Slave thirteen
    // Wishbone Slave interface
    wbs12_adr_i,
    wbs12_dat_i,
    wbs12_sel_i,		    
    wbs12_we_i,
    wbs12_cyc_i,
    wbs12_stb_i,
    wbs12_cti_i,
    wbs12_bte_i,
  
    wbs12_dat_o,
    wbs12_ack_o,
    wbs12_err_o,
    wbs12_rty_o,

    // Slave fourteen
    // Wishbone Slave interface
    wbs13_adr_i,
    wbs13_dat_i,
    wbs13_sel_i,		    
    wbs13_we_i,
    wbs13_cyc_i,
    wbs13_stb_i,
    wbs13_cti_i,
    wbs13_bte_i,
  
    wbs13_dat_o,
    wbs13_ack_o,
    wbs13_err_o,
    wbs13_rty_o,

    // Slave fifteen
    // Wishbone Slave interface
    wbs14_adr_i,
    wbs14_dat_i,
    wbs14_sel_i,		    
    wbs14_we_i,
    wbs14_cyc_i,
    wbs14_stb_i,
    wbs14_cti_i,
    wbs14_bte_i,
  
    wbs14_dat_o,
    wbs14_ack_o,
    wbs14_err_o,
    wbs14_rty_o,

    // Slave sixteen
    // Wishbone Slave interface
    wbs15_adr_i,
    wbs15_dat_i,
    wbs15_sel_i,		    
    wbs15_we_i,
    wbs15_cyc_i,
    wbs15_stb_i,
    wbs15_cti_i,
    wbs15_bte_i,
  
    wbs15_dat_o,
    wbs15_ack_o,
    wbs15_err_o,
    wbs15_rty_o,

    // Slave seventeen
    // Wishbone Slave interface
    wbs16_adr_i,
    wbs16_dat_i,
    wbs16_sel_i,		    
    wbs16_we_i,
    wbs16_cyc_i,
    wbs16_stb_i,
    wbs16_cti_i,
    wbs16_bte_i,
  
    wbs16_dat_o,
    wbs16_ack_o,
    wbs16_err_o,
    wbs16_rty_o,
    */		    
  
   wb_clk,
   wb_rst
   );

   parameter wb_dat_width = 32;
   parameter wb_adr_width = 32;

   parameter wb_addr_match_width = 8;

   parameter wb_num_slaves = 2; // must also (un)comment things if changing

   // Slave addresses - these should be defparam'd from top level
   // Declare them as you need them
   parameter slave0_adr = 0;
   parameter slave1_adr = 0;
   parameter slave2_adr = 0;
   parameter slave3_adr = 0;
   parameter slave4_adr = 0;
   parameter slave5_adr = 0;
   parameter slave6_adr = 0;
   parameter slave7_adr = 0;
   parameter slave8_adr = 0;
   parameter slave9_adr = 0;
   parameter slave10_adr = 0;   
   parameter slave11_adr = 0;
   parameter slave12_adr = 0;

   // Select for slave 0
`define WB_ARB_ADDR_MATCH_SEL_SLAVE0 wb_adr_width-1:wb_adr_width-4
`define WB_ARB_ADDR_MATCH_SEL wb_adr_width-1:wb_adr_width-wb_addr_match_width

   input wb_clk;
   input wb_rst;
   
   // WB Master one
   input [wb_adr_width-1:0] wbm0_adr_o;
   input [wb_dat_width-1:0] wbm0_dat_o;
   input [3:0] 		    wbm0_sel_o;
   input 		    wbm0_we_o;
   input 		    wbm0_cyc_o;
   input 		    wbm0_stb_o;
   input [2:0] 		    wbm0_cti_o;
   input [1:0] 		    wbm0_bte_o;
   output [wb_dat_width-1:0] wbm0_dat_i;   
   output 		     wbm0_ack_i;
   output 		     wbm0_err_i;
   output 		     wbm0_rty_i;   
   
   
   input [wb_adr_width-1:0]  wbm1_adr_o;
   input [wb_dat_width-1:0]  wbm1_dat_o;
   input [3:0] 		     wbm1_sel_o;   
   input 		     wbm1_we_o;
   input 		     wbm1_cyc_o;
   input 		     wbm1_stb_o;
   input [2:0] 		     wbm1_cti_o;
   input [1:0] 		     wbm1_bte_o;
   output [wb_dat_width-1:0] wbm1_dat_i;   
   output 		     wbm1_ack_i;
   output 		     wbm1_err_i;
   output 		     wbm1_rty_i;   

   
   // Slave one
   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs0_adr_i;
   output [wb_dat_width-1:0] wbs0_dat_i;
   output [3:0]		     wbs0_sel_i;
   output 		     wbs0_we_i;
   output 		     wbs0_cyc_i;
   output 		     wbs0_stb_i;
   output [2:0] 	     wbs0_cti_i;
   output [1:0] 	     wbs0_bte_i;
   input [wb_dat_width-1:0]  wbs0_dat_o;
   input 		     wbs0_ack_o;
   input 		     wbs0_err_o;
   input 		     wbs0_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs1_adr_i;
   output [wb_dat_width-1:0] wbs1_dat_i;
   output [3:0]		     wbs1_sel_i;
   output 		     wbs1_we_i;
   output 		     wbs1_cyc_i;
   output 		     wbs1_stb_i;
   output [2:0] 	     wbs1_cti_i;
   output [1:0] 	     wbs1_bte_i;
   input [wb_dat_width-1:0]  wbs1_dat_o;
   input 		     wbs1_ack_o;
   input 		     wbs1_err_o;
   input 		     wbs1_rty_o;
   
/*   
   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs2_adr_i;
   output [wb_dat_width-1:0] wbs2_dat_i;
   output [3:0]		     wbs2_sel_i;
   output 		     wbs2_we_i;
   output 		     wbs2_cyc_i;
   output 		     wbs2_stb_i;
   output [2:0] 	     wbs2_cti_i;
   output [1:0] 	     wbs2_bte_i;
   input [wb_dat_width-1:0]  wbs2_dat_o;
   input 		     wbs2_ack_o;
   input 		     wbs2_err_o;
   input 		     wbs2_rty_o;

 
   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs3_adr_i;
   output [wb_dat_width-1:0] wbs3_dat_i;
   output [3:0]		     wbs3_sel_i;
   output 		     wbs3_we_i;
   output 		     wbs3_cyc_i;
   output 		     wbs3_stb_i;
   output [2:0] 	     wbs3_cti_i;
   output [1:0] 	     wbs3_bte_i;
   input [wb_dat_width-1:0]  wbs3_dat_o;
   input 		     wbs3_ack_o;
   input 		     wbs3_err_o;
   input 		     wbs3_rty_o;

 
   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs4_adr_i;
   output [wb_dat_width-1:0] wbs4_dat_i;
   output [3:0]		     wbs4_sel_i;
   output 		     wbs4_we_i;
   output 		     wbs4_cyc_i;
   output 		     wbs4_stb_i;
   output [2:0] 	     wbs4_cti_i;
   output [1:0] 	     wbs4_bte_i;
   input [wb_dat_width-1:0]  wbs4_dat_o;
   input 		     wbs4_ack_o;
   input 		     wbs4_err_o;
   input 		     wbs4_rty_o;

 
   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs5_adr_i;
   output [wb_dat_width-1:0] wbs5_dat_i;
   output [3:0]		     wbs5_sel_i;
   output 		     wbs5_we_i;
   output 		     wbs5_cyc_i;
   output 		     wbs5_stb_i;
   output [2:0] 	     wbs5_cti_i;
   output [1:0] 	     wbs5_bte_i;
   input [wb_dat_width-1:0]  wbs5_dat_o;
   input 		     wbs5_ack_o;
   input 		     wbs5_err_o;
   input 		     wbs5_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs6_adr_i;
   output [wb_dat_width-1:0] wbs6_dat_i;
   output [3:0]		     wbs6_sel_i;
   output 		     wbs6_we_i;
   output 		     wbs6_cyc_i;
   output 		     wbs6_stb_i;
   output [2:0] 	     wbs6_cti_i;
   output [1:0] 	     wbs6_bte_i;
   input [wb_dat_width-1:0]  wbs6_dat_o;
   input 		     wbs6_ack_o;
   input 		     wbs6_err_o;
   input 		     wbs6_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs7_adr_i;
   output [wb_dat_width-1:0] wbs7_dat_i;
   output [3:0]		     wbs7_sel_i;
   output 		     wbs7_we_i;
   output 		     wbs7_cyc_i;
   output 		     wbs7_stb_i;
   output [2:0] 	     wbs7_cti_i;
   output [1:0] 	     wbs7_bte_i;
   input [wb_dat_width-1:0]  wbs7_dat_o;
   input 		     wbs7_ack_o;
   input 		     wbs7_err_o;
   input 		     wbs7_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs8_adr_i;
   output [wb_dat_width-1:0] wbs8_dat_i;
   output [3:0]		     wbs8_sel_i;
   output 		     wbs8_we_i;
   output 		     wbs8_cyc_i;
   output 		     wbs8_stb_i;
   output [2:0] 	     wbs8_cti_i;
   output [1:0] 	     wbs8_bte_i;
   input [wb_dat_width-1:0]  wbs8_dat_o;
   input 		     wbs8_ack_o;
   input 		     wbs8_err_o;
   input 		     wbs8_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs9_adr_i;
   output [wb_dat_width-1:0] wbs9_dat_i;
   output [3:0]		     wbs9_sel_i;
   output 		     wbs9_we_i;
   output 		     wbs9_cyc_i;
   output 		     wbs9_stb_i;
   output [2:0] 	     wbs9_cti_i;
   output [1:0] 	     wbs9_bte_i;
   input [wb_dat_width-1:0]  wbs9_dat_o;
   input 		     wbs9_ack_o;
   input 		     wbs9_err_o;
   input 		     wbs9_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs10_adr_i;
   output [wb_dat_width-1:0] wbs10_dat_i;
   output [3:0]		     wbs10_sel_i;
   output 		     wbs10_we_i;
   output 		     wbs10_cyc_i;
   output 		     wbs10_stb_i;
   output [2:0] 	     wbs10_cti_i;
   output [1:0] 	     wbs10_bte_i;
   input [wb_dat_width-1:0]  wbs10_dat_o;
   input 		     wbs10_ack_o;
   input 		     wbs10_err_o;
   input 		     wbs10_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs11_adr_i;
   output [wb_dat_width-1:0] wbs11_dat_i;
   output [3:0]		     wbs11_sel_i;
   output 		     wbs11_we_i;
   output 		     wbs11_cyc_i;
   output 		     wbs11_stb_i;
   output [2:0] 	     wbs11_cti_i;
   output [1:0] 	     wbs11_bte_i;
   input [wb_dat_width-1:0]  wbs11_dat_o;
   input 		     wbs11_ack_o;
   input 		     wbs11_err_o;
   input 		     wbs11_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs12_adr_i;
   output [wb_dat_width-1:0] wbs12_dat_i;
   output [3:0]		     wbs12_sel_i;
   output 		     wbs12_we_i;
   output 		     wbs12_cyc_i;
   output 		     wbs12_stb_i;
   output [2:0] 	     wbs12_cti_i;
   output [1:0] 	     wbs12_bte_i;
   input [wb_dat_width-1:0]  wbs12_dat_o;
   input 		     wbs12_ack_o;
   input 		     wbs12_err_o;
   input 		     wbs12_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs13_adr_i;
   output [wb_dat_width-1:0] wbs13_dat_i;
   output [3:0]		     wbs13_sel_i;
   output 		     wbs13_we_i;
   output 		     wbs13_cyc_i;
   output 		     wbs13_stb_i;
   output [2:0] 	     wbs13_cti_i;
   output [1:0] 	     wbs13_bte_i;
   input [wb_dat_width-1:0]  wbs13_dat_o;
   input 		     wbs13_ack_o;
   input 		     wbs13_err_o;
   input 		     wbs13_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs14_adr_i;
   output [wb_dat_width-1:0] wbs14_dat_i;
   output [3:0]		     wbs14_sel_i;
   output 		     wbs14_we_i;
   output 		     wbs14_cyc_i;
   output 		     wbs14_stb_i;
   output [2:0] 	     wbs14_cti_i;
   output [1:0] 	     wbs14_bte_i;
   input [wb_dat_width-1:0]  wbs14_dat_o;
   input 		     wbs14_ack_o;
   input 		     wbs14_err_o;
   input 		     wbs14_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs15_adr_i;
   output [wb_dat_width-1:0] wbs15_dat_i;
   output [3:0]		     wbs15_sel_i;
   output 		     wbs15_we_i;
   output 		     wbs15_cyc_i;
   output 		     wbs15_stb_i;
   output [2:0] 	     wbs15_cti_i;
   output [1:0] 	     wbs15_bte_i;
   input [wb_dat_width-1:0]  wbs15_dat_o;
   input 		     wbs15_ack_o;
   input 		     wbs15_err_o;
   input 		     wbs15_rty_o;
   

   // Wishbone Slave interface
   output [wb_adr_width-1:0] wbs16_adr_i;
   output [wb_dat_width-1:0] wbs16_dat_i;
   output [3:0]		     wbs16_sel_i;
   output 		     wbs16_we_i;
   output 		     wbs16_cyc_i;
   output 		     wbs16_stb_i;
   output [2:0] 	     wbs16_cti_i;
   output [1:0] 	     wbs16_bte_i;
   input [wb_dat_width-1:0]  wbs16_dat_o;
   input 		     wbs16_ack_o;
   input 		     wbs16_err_o;
   input 		     wbs16_rty_o;
   
*/

   reg 		     watchdog_err;
   
`ifdef ARBITER_DBUS_REGISTERING

   
   // Registering setup:
   // Masters typically register their outputs, so do the master selection and
   // muxing before registering in the arbiter. Keep the common parts outside
   // for code brevity.
   
   // Master ins -> |MUX> -> these wires
   wire [wb_adr_width-1:0]   wbm_adr_o_w;
   wire [wb_dat_width-1:0]   wbm_dat_o_w;
   wire [3:0] 		     wbm_sel_o_w;
   wire 		     wbm_we_o_w;
   wire 		     wbm_cyc_o_w;
   wire 		     wbm_stb_o_w;
   wire [2:0] 		     wbm_cti_o_w;
   wire [1:0] 		     wbm_bte_o_w;
   // Slave ins -> |MUX> -> these wires
   wire [wb_dat_width-1:0]   wbm_dat_i;   
   wire 		     wbm_ack_i;
   wire 		     wbm_err_i;
   wire 		     wbm_rty_i;   

   // Registers after masters input mux
   reg [wb_adr_width-1:0]    wbm_adr_o_r;
   reg [wb_dat_width-1:0]    wbm_dat_o_r;
   reg [3:0] 		     wbm_sel_o_r;   
   reg 			     wbm_we_o_r;
   reg 			     wbm_cyc_o_r;
   reg 			     wbm_stb_o_r;
   reg [2:0] 		     wbm_cti_o_r;
   reg [1:0] 		     wbm_bte_o_r;

   // Master input mux register wires
   wire [wb_adr_width-1:0]   wbm_adr_o;
   wire [wb_dat_width-1:0]   wbm_dat_o;
   wire [3:0] 		     wbm_sel_o;
   wire 		     wbm_we_o;
   wire 		     wbm_cyc_o;
   wire 		     wbm_stb_o;
   wire [2:0] 		     wbm_cti_o;
   wire [1:0] 		     wbm_bte_o;

   // Registers after slaves input mux
   reg [wb_dat_width-1:0]    wbm_dat_i_r;   
   reg 			     wbm_ack_i_r;
   reg 			     wbm_err_i_r;
   reg 			     wbm_rty_i_r;

   // Master select (MUX controls)
   wire [1:0] 		     master_sel;
   // priority to wbm1, the debug master
   assign master_sel[0] = wbm0_cyc_o & !wbm1_cyc_o;
   assign master_sel[1] = wbm1_cyc_o;


   // Master input mux, priority to debug master
   assign wbm_adr_o_w = master_sel[1] ? wbm1_adr_o :
		      wbm0_adr_o;
   
   assign wbm_dat_o_w = master_sel[1] ? wbm1_dat_o :
		      wbm0_dat_o;
   
   assign wbm_sel_o_w = master_sel[1] ? wbm1_sel_o :
		      wbm0_sel_o;

   assign wbm_we_o_w = master_sel[1] ? wbm1_we_o :
		      wbm0_we_o;
   
   assign wbm_cyc_o_w = master_sel[1] ? wbm1_cyc_o :
		      wbm0_cyc_o;

   assign wbm_stb_o_w = master_sel[1] ? wbm1_stb_o :
		     wbm0_stb_o;

   assign wbm_cti_o_w = master_sel[1] ? wbm1_cti_o :
		     wbm0_cti_o;

   assign wbm_bte_o_w = master_sel[1] ? wbm1_bte_o :
		      wbm0_bte_o;

   
   // Register muxed master signals
   always @(posedge wb_clk)
     begin
	wbm_adr_o_r <= wbm_adr_o_w;
	wbm_dat_o_r <= wbm_dat_o_w;
	wbm_sel_o_r <= wbm_sel_o_w;
	wbm_we_o_r <= wbm_we_o_w;
	wbm_cyc_o_r <= wbm_cyc_o_w;	
	wbm_stb_o_r <= wbm_stb_o_w & !wbm_ack_i & !wbm_ack_i_r;
	wbm_cti_o_r <= wbm_cti_o_w;
	wbm_bte_o_r <= wbm_bte_o_w;
	
	wbm_dat_i_r <= wbm_dat_i;
	wbm_ack_i_r <= wbm_ack_i;
	wbm_err_i_r <= wbm_err_i;
	wbm_rty_i_r <= wbm_rty_i;
     end // always @ (posedge wb_clk)

   
   assign wbm_adr_o = wbm_adr_o_r;
   assign wbm_dat_o = wbm_dat_o_r;
   assign wbm_sel_o = wbm_sel_o_r;
   assign wbm_we_o = wbm_we_o_r;
   assign wbm_cyc_o = wbm_cyc_o_r;
   assign wbm_stb_o = wbm_stb_o_r;
   assign wbm_cti_o = wbm_cti_o_r;
   assign wbm_bte_o = wbm_bte_o_r;

   // Master input mux, priority to debug master
   assign wbm0_dat_i = wbm_dat_i_r;
   assign wbm0_ack_i = wbm_ack_i_r & master_sel[0];
   assign wbm0_err_i = wbm_err_i_r & master_sel[0];
   assign wbm0_rty_i = wbm_rty_i_r & master_sel[0];
   
   assign wbm1_dat_i = wbm_dat_i_r;
   assign wbm1_ack_i = wbm_ack_i_r & master_sel[1];
   assign wbm1_err_i = wbm_err_i_r & master_sel[1];
   assign wbm1_rty_i = wbm_rty_i_r & master_sel[1];
   
`else // !`ifdef ARBITER_DBUS_REGISTERING

   // Master input mux output wires
   wire [wb_adr_width-1:0]   wbm_adr_o;
   wire [wb_dat_width-1:0]   wbm_dat_o;
   wire [3:0] 		     wbm_sel_o;
   wire 		     wbm_we_o;
   wire 		     wbm_cyc_o;
   wire 		     wbm_stb_o;
   wire [2:0] 		     wbm_cti_o;
   wire [1:0] 		     wbm_bte_o;
   
   // Master select
   wire [1:0] 		     master_sel;
   // priority to wbm1, the debug master
   assign master_sel[0] = wbm0_cyc_o & !wbm1_cyc_o;
   assign master_sel[1] = wbm1_cyc_o;


   // Master input mux, priority to debug master
   assign wbm_adr_o = master_sel[1] ? wbm1_adr_o :
		      wbm0_adr_o;
   
   assign wbm_dat_o = master_sel[1] ? wbm1_dat_o :
		      wbm0_dat_o;
   
   assign wbm_sel_o = master_sel[1] ? wbm1_sel_o :
		      wbm0_sel_o;

   assign wbm_we_o = master_sel[1] ? wbm1_we_o :
		      wbm0_we_o;
   
   assign wbm_cyc_o = master_sel[1] ? wbm1_cyc_o :
		      wbm0_cyc_o;

   assign wbm_stb_o = master_sel[1] ? wbm1_stb_o :
		     wbm0_stb_o;

   assign wbm_cti_o = master_sel[1] ? wbm1_cti_o :
		     wbm0_cti_o;

   assign wbm_bte_o = master_sel[1] ? wbm1_bte_o :
		      wbm0_bte_o;


   wire [wb_dat_width-1:0]   wbm_dat_i;   
   wire 		     wbm_ack_i;
   wire 		     wbm_err_i;
   wire 		     wbm_rty_i;   


   assign wbm0_dat_i = wbm_dat_i;
   assign wbm0_ack_i = wbm_ack_i & master_sel[0];
   assign wbm0_err_i = wbm_err_i & master_sel[0];
   assign wbm0_rty_i = wbm_rty_i & master_sel[0];
   
   assign wbm1_dat_i = wbm_dat_i;
   assign wbm1_ack_i = wbm_ack_i & master_sel[1];
   assign wbm1_err_i = wbm_err_i & master_sel[1];
   assign wbm1_rty_i = wbm_rty_i & master_sel[1];

   

`endif // !`ifdef ARBITER_DBUS_REGISTERING

  
   // Slave select wire
   wire [wb_num_slaves-1:0]  wb_slave_sel;
   reg [wb_num_slaves-1:0]   wb_slave_sel_r;

   // Register wb_slave_sel_r to break combinatorial loop when selecting default
   // slave
   always @(posedge wb_clk)
     wb_slave_sel_r <= wb_slave_sel;
   
   // Slave out mux in wires   
   wire [wb_dat_width-1:0]   wbs_dat_o_mux_i [0:wb_num_slaves-1];
   wire 		     wbs_ack_o_mux_i [0:wb_num_slaves-1];
   wire 		     wbs_err_o_mux_i [0:wb_num_slaves-1];
   wire 		     wbs_rty_o_mux_i [0:wb_num_slaves-1];

   //
   // Slave selects
   //
   assign wb_slave_sel[0] = wbm_adr_o[31:28] == slave0_adr | wbm_adr_o[31:28] == 4'hf; // Special case, point all reads to ROM address to here
   
   // Auto select last slave when others are not selected
   assign wb_slave_sel[1] = !(wb_slave_sel_r[0]);

/*
   assign wb_slave_sel[1] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave1_adr;
   assign wb_slave_sel[2] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave2_adr;   
   assign wb_slave_sel[3] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave3_adr;   
   assign wb_slave_sel[4] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave4_adr;
   assign wb_slave_sel[5] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave5_adr;
   assign wb_slave_sel[6] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave6_adr;
   assign wb_slave_sel[7] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave7_adr;
   assign wb_slave_sel[8] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave8_adr;
   assign wb_slave_sel[9] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave9_adr;
   assign wb_slave_sel[10] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave10_adr;
   assign wb_slave_sel[11] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave11_adr;
   assign wb_slave_sel[12] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave12_adr;
   assign wb_slave_sel[13] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave13_adr;
   assign wb_slave_sel[14] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave14_adr;
   assign wb_slave_sel[15] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave15_adr;
   assign wb_slave_sel[16] = wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == slave16_adr;
*/

`ifdef ARBITER_DBUS_WATCHDOG
   reg [`ARBITER_DBUS_WATCHDOG_TIMER_WIDTH:0] watchdog_timer;
   reg 			     wbm_stb_r; // Register strobe
   wire 		     wbm_stb_edge; // Detect its edge

   always @(posedge wb_clk)
     wbm_stb_r <= wbm_stb_o;

   assign wbm_stb_edge = (wbm_stb_o & !wbm_stb_r);
   
   // Counter logic
   always @(posedge wb_clk)
     if (wb_rst) watchdog_timer <= 0;
     else if (wbm_ack_i) // When we see an ack, turn off timer
       watchdog_timer <= 0;
     else if (wbm_stb_edge) // New access means start timer again
       watchdog_timer <= 1;
     else if (|watchdog_timer) // Continue counting if counter > 0
       watchdog_timer <= watchdog_timer + 1;

   always @(posedge wb_clk) 
     watchdog_err <= (&watchdog_timer);

   
`else // !`ifdef ARBITER_DBUS_WATCHDOG
   
   always @(posedge wb_clk) 
     watchdog_err <= 0;
   
`endif // !`ifdef ARBITER_DBUS_WATCHDOG
   

   
   // Slave 0 inputs
   assign wbs0_adr_i = wbm_adr_o;
   assign wbs0_dat_i = wbm_dat_o;
   assign wbs0_sel_i = wbm_sel_o;
   assign wbs0_cyc_i = wbm_cyc_o & wb_slave_sel_r[0];
   assign wbs0_stb_i = wbm_stb_o & wb_slave_sel_r[0];   
   assign wbs0_we_i =  wbm_we_o;
   assign wbs0_cti_i = wbm_cti_o;
   assign wbs0_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[0] = wbs0_dat_o;
   assign wbs_ack_o_mux_i[0] = wbs0_ack_o & wb_slave_sel_r[0];
   assign wbs_err_o_mux_i[0] = wbs0_err_o & wb_slave_sel_r[0];
   assign wbs_rty_o_mux_i[0] = wbs0_rty_o & wb_slave_sel_r[0];


   // Slave 1 inputs
   assign wbs1_adr_i = wbm_adr_o;
   assign wbs1_dat_i = wbm_dat_o;
   assign wbs1_sel_i = wbm_sel_o;
   assign wbs1_cyc_i = wbm_cyc_o & wb_slave_sel_r[1];
   assign wbs1_stb_i = wbm_stb_o & wb_slave_sel_r[1];   
   assign wbs1_we_i =  wbm_we_o;
   assign wbs1_cti_i = wbm_cti_o;
   assign wbs1_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[1] = wbs1_dat_o;
   assign wbs_ack_o_mux_i[1] = wbs1_ack_o & wb_slave_sel_r[1];
   assign wbs_err_o_mux_i[1] = wbs1_err_o & wb_slave_sel_r[1];
   assign wbs_rty_o_mux_i[1] = wbs1_rty_o & wb_slave_sel_r[1];

/*
   // Slave 2 inputs
   assign wbs2_adr_i = wbm_adr_o;
   assign wbs2_dat_i = wbm_dat_o;
   assign wbs2_sel_i = wbm_sel_o;
   assign wbs2_cyc_i = wbm_cyc_o & wb_slave_sel_r[2];
   assign wbs2_stb_i = wbm_stb_o & wb_slave_sel_r[2];   
   assign wbs2_we_i =  wbm_we_o;
   assign wbs2_cti_i = wbm_cti_o;
   assign wbs2_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[2] = wbs2_dat_o;
   assign wbs_ack_o_mux_i[2] = wbs2_ack_o & wb_slave_sel_r[2];
   assign wbs_err_o_mux_i[2] = wbs2_err_o & wb_slave_sel_r[2];
   assign wbs_rty_o_mux_i[2] = wbs2_rty_o & wb_slave_sel_r[2];


   // Slave 3 inputs
   assign wbs3_adr_i = wbm_adr_o;
   assign wbs3_dat_i = wbm_dat_o;
   assign wbs3_sel_i = wbm_sel_o;
   assign wbs3_cyc_i = wbm_cyc_o & wb_slave_sel_r[3];
   assign wbs3_stb_i = wbm_stb_o & wb_slave_sel_r[3];   
   assign wbs3_we_i =  wbm_we_o;
   assign wbs3_cti_i = wbm_cti_o;
   assign wbs3_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[3] = wbs3_dat_o;
   assign wbs_ack_o_mux_i[3] = wbs3_ack_o & wb_slave_sel_r[3];
   assign wbs_err_o_mux_i[3] = wbs3_err_o & wb_slave_sel_r[3];
   assign wbs_rty_o_mux_i[3] = wbs3_rty_o & wb_slave_sel_r[3];

   // Slave 4 inputs
   assign wbs4_adr_i = wbm_adr_o;
   assign wbs4_dat_i = wbm_dat_o;
   assign wbs4_sel_i = wbm_sel_o;
   assign wbs4_cyc_i = wbm_cyc_o & wb_slave_sel_r[4];
   assign wbs4_stb_i = wbm_stb_o & wb_slave_sel_r[4];   
   assign wbs4_we_i =  wbm_we_o;
   assign wbs4_cti_i = wbm_cti_o;
   assign wbs4_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[4] = wbs4_dat_o;
   assign wbs_ack_o_mux_i[4] = wbs4_ack_o & wb_slave_sel_r[4];
   assign wbs_err_o_mux_i[4] = wbs4_err_o & wb_slave_sel_r[4];
   assign wbs_rty_o_mux_i[4] = wbs4_rty_o & wb_slave_sel_r[4];


   // Slave 5 inputs
   assign wbs5_adr_i = wbm_adr_o;
   assign wbs5_dat_i = wbm_dat_o;
   assign wbs5_sel_i = wbm_sel_o;
   assign wbs5_cyc_i = wbm_cyc_o & wb_slave_sel_r[5];
   assign wbs5_stb_i = wbm_stb_o & wb_slave_sel_r[5];   
   assign wbs5_we_i =  wbm_we_o;
   assign wbs5_cti_i = wbm_cti_o;
   assign wbs5_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[5] = wbs5_dat_o;
   assign wbs_ack_o_mux_i[5] = wbs5_ack_o & wb_slave_sel_r[5];
   assign wbs_err_o_mux_i[5] = wbs5_err_o & wb_slave_sel_r[5];
   assign wbs_rty_o_mux_i[5] = wbs5_rty_o & wb_slave_sel_r[5];


   // Slave 6 inputs
   assign wbs6_adr_i = wbm_adr_o;
   assign wbs6_dat_i = wbm_dat_o;
   assign wbs6_sel_i = wbm_sel_o;
   assign wbs6_cyc_i = wbm_cyc_o & wb_slave_sel_r[6];
   assign wbs6_stb_i = wbm_stb_o & wb_slave_sel_r[6];   
   assign wbs6_we_i =  wbm_we_o;
   assign wbs6_cti_i = wbm_cti_o;
   assign wbs6_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[6] = wbs6_dat_o;
   assign wbs_ack_o_mux_i[6] = wbs6_ack_o & wb_slave_sel_r[6];
   assign wbs_err_o_mux_i[6] = wbs6_err_o & wb_slave_sel_r[6];
   assign wbs_rty_o_mux_i[6] = wbs6_rty_o & wb_slave_sel_r[6];


   // Slave 7 inputs
   assign wbs7_adr_i = wbm_adr_o;
   assign wbs7_dat_i = wbm_dat_o;
   assign wbs7_sel_i = wbm_sel_o;
   assign wbs7_cyc_i = wbm_cyc_o & wb_slave_sel_r[7];
   assign wbs7_stb_i = wbm_stb_o & wb_slave_sel_r[7];   
   assign wbs7_we_i =  wbm_we_o;
   assign wbs7_cti_i = wbm_cti_o;
   assign wbs7_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[7] = wbs7_dat_o;
   assign wbs_ack_o_mux_i[7] = wbs7_ack_o & wb_slave_sel_r[7];
   assign wbs_err_o_mux_i[7] = wbs7_err_o & wb_slave_sel_r[7];
   assign wbs_rty_o_mux_i[7] = wbs7_rty_o & wb_slave_sel_r[7];


   // Slave 8 inputs
   assign wbs8_adr_i = wbm_adr_o;
   assign wbs8_dat_i = wbm_dat_o;
   assign wbs8_sel_i = wbm_sel_o;
   assign wbs8_cyc_i = wbm_cyc_o & wb_slave_sel_r[8];
   assign wbs8_stb_i = wbm_stb_o & wb_slave_sel_r[8];   
   assign wbs8_we_i =  wbm_we_o;
   assign wbs8_cti_i = wbm_cti_o;
   assign wbs8_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[8] = wbs8_dat_o;
   assign wbs_ack_o_mux_i[8] = wbs8_ack_o & wb_slave_sel_r[8];
   assign wbs_err_o_mux_i[8] = wbs8_err_o & wb_slave_sel_r[8];
   assign wbs_rty_o_mux_i[8] = wbs8_rty_o & wb_slave_sel_r[8];


   // Slave 9 inputs
   assign wbs9_adr_i = wbm_adr_o;
   assign wbs9_dat_i = wbm_dat_o;
   assign wbs9_sel_i = wbm_sel_o;
   assign wbs9_cyc_i = wbm_cyc_o & wb_slave_sel_r[9];
   assign wbs9_stb_i = wbm_stb_o & wb_slave_sel_r[9];   
   assign wbs9_we_i =  wbm_we_o;
   assign wbs9_cti_i = wbm_cti_o;
   assign wbs9_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[9] = wbs9_dat_o;
   assign wbs_ack_o_mux_i[9] = wbs9_ack_o & wb_slave_sel_r[9];
   assign wbs_err_o_mux_i[9] = wbs9_err_o & wb_slave_sel_r[9];
   assign wbs_rty_o_mux_i[9] = wbs9_rty_o & wb_slave_sel_r[9];


   // Slave 10 inputs
   assign wbs10_adr_i = wbm_adr_o;
   assign wbs10_dat_i = wbm_dat_o;
   assign wbs10_sel_i = wbm_sel_o;
   assign wbs10_cyc_i = wbm_cyc_o & wb_slave_sel_r[10];
   assign wbs10_stb_i = wbm_stb_o & wb_slave_sel_r[10];   
   assign wbs10_we_i =  wbm_we_o;
   assign wbs10_cti_i = wbm_cti_o;
   assign wbs10_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[10] = wbs10_dat_o;
   assign wbs_ack_o_mux_i[10] = wbs10_ack_o & wb_slave_sel_r[10];
   assign wbs_err_o_mux_i[10] = wbs10_err_o & wb_slave_sel_r[10];
   assign wbs_rty_o_mux_i[10] = wbs10_rty_o & wb_slave_sel_r[10];

   
   // Slave 11 inputs
   assign wbs11_adr_i = wbm_adr_o;
   assign wbs11_dat_i = wbm_dat_o;
   assign wbs11_sel_i = wbm_sel_o;
   assign wbs11_cyc_i = wbm_cyc_o & wb_slave_sel_r[11];
   assign wbs11_stb_i = wbm_stb_o & wb_slave_sel_r[11];   
   assign wbs11_we_i =  wbm_we_o;
   assign wbs11_cti_i = wbm_cti_o;
   assign wbs11_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[11] = wbs11_dat_o;
   assign wbs_ack_o_mux_i[11] = wbs11_ack_o & wb_slave_sel_r[11];
   assign wbs_err_o_mux_i[11] = wbs11_err_o & wb_slave_sel_r[11];
   assign wbs_rty_o_mux_i[11] = wbs11_rty_o & wb_slave_sel_r[11];


   // Slave 12 inputs
   assign wbs12_adr_i = wbm_adr_o;
   assign wbs12_dat_i = wbm_dat_o;
   assign wbs12_sel_i = wbm_sel_o;
   assign wbs12_cyc_i = wbm_cyc_o & wb_slave_sel_r[12];
   assign wbs12_stb_i = wbm_stb_o & wb_slave_sel_r[12];   
   assign wbs12_we_i =  wbm_we_o;
   assign wbs12_cti_i = wbm_cti_o;
   assign wbs12_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[12] = wbs12_dat_o;
   assign wbs_ack_o_mux_i[12] = wbs12_ack_o & wb_slave_sel_r[12];
   assign wbs_err_o_mux_i[12] = wbs12_err_o & wb_slave_sel_r[12];
   assign wbs_rty_o_mux_i[12] = wbs12_rty_o & wb_slave_sel_r[12];


   // Slave 13 inputs
   assign wbs13_adr_i = wbm_adr_o;
   assign wbs13_dat_i = wbm_dat_o;
   assign wbs13_sel_i = wbm_sel_o;
   assign wbs13_cyc_i = wbm_cyc_o & wb_slave_sel_r[13];
   assign wbs13_stb_i = wbm_stb_o & wb_slave_sel_r[13];   
   assign wbs13_we_i =  wbm_we_o;
   assign wbs13_cti_i = wbm_cti_o;
   assign wbs13_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[13] = wbs13_dat_o;
   assign wbs_ack_o_mux_i[13] = wbs13_ack_o & wb_slave_sel_r[13];
   assign wbs_err_o_mux_i[13] = wbs13_err_o & wb_slave_sel_r[13];
   assign wbs_rty_o_mux_i[13] = wbs13_rty_o & wb_slave_sel_r[13];


   // Slave 14 inputs
   assign wbs14_adr_i = wbm_adr_o;
   assign wbs14_dat_i = wbm_dat_o;
   assign wbs14_sel_i = wbm_sel_o;
   assign wbs14_cyc_i = wbm_cyc_o & wb_slave_sel_r[14];
   assign wbs14_stb_i = wbm_stb_o & wb_slave_sel_r[14];   
   assign wbs14_we_i =  wbm_we_o;
   assign wbs14_cti_i = wbm_cti_o;
   assign wbs14_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[14] = wbs14_dat_o;
   assign wbs_ack_o_mux_i[14] = wbs14_ack_o & wb_slave_sel_r[14];
   assign wbs_err_o_mux_i[14] = wbs14_err_o & wb_slave_sel_r[14];
   assign wbs_rty_o_mux_i[14] = wbs14_rty_o & wb_slave_sel_r[14];


   // Slave 15 inputs
   assign wbs15_adr_i = wbm_adr_o;
   assign wbs15_dat_i = wbm_dat_o;
   assign wbs15_sel_i = wbm_sel_o;
   assign wbs15_cyc_i = wbm_cyc_o & wb_slave_sel_r[15];
   assign wbs15_stb_i = wbm_stb_o & wb_slave_sel_r[15];   
   assign wbs15_we_i =  wbm_we_o;
   assign wbs15_cti_i = wbm_cti_o;
   assign wbs15_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[15] = wbs15_dat_o;
   assign wbs_ack_o_mux_i[15] = wbs15_ack_o & wb_slave_sel_r[15];
   assign wbs_err_o_mux_i[15] = wbs15_err_o & wb_slave_sel_r[15];
   assign wbs_rty_o_mux_i[15] = wbs15_rty_o & wb_slave_sel_r[15];


   // Slave 16 inputs
   assign wbs16_adr_i = wbm_adr_o;
   assign wbs16_dat_i = wbm_dat_o;
   assign wbs16_sel_i = wbm_sel_o;
   assign wbs16_cyc_i = wbm_cyc_o & wb_slave_sel_r[16];
   assign wbs16_stb_i = wbm_stb_o & wb_slave_sel_r[16];   
   assign wbs16_we_i =  wbm_we_o;
   assign wbs16_cti_i = wbm_cti_o;
   assign wbs16_bte_i = wbm_bte_o;
   assign wbs_dat_o_mux_i[16] = wbs16_dat_o;
   assign wbs_ack_o_mux_i[16] = wbs16_ack_o & wb_slave_sel_r[16];
   assign wbs_err_o_mux_i[16] = wbs16_err_o & wb_slave_sel_r[16];
   assign wbs_rty_o_mux_i[16] = wbs16_rty_o & wb_slave_sel_r[16];

*/



   // Master out mux from slave in data
   assign wbm_dat_i = wb_slave_sel_r[0] ? wbs_dat_o_mux_i[0] :
		      wb_slave_sel_r[1] ? wbs_dat_o_mux_i[1] :
/*		      wb_slave_sel_r[2] ? wbs_dat_o_mux_i[2] :
		      wb_slave_sel_r[3] ? wbs_dat_o_mux_i[3] :
 		      wb_slave_sel_r[4] ? wbs_dat_o_mux_i[4] :
		      wb_slave_sel_r[5] ? wbs_dat_o_mux_i[5] :
		      wb_slave_sel_r[6] ? wbs_dat_o_mux_i[6] :
		      wb_slave_sel_r[7] ? wbs_dat_o_mux_i[7] :
		      wb_slave_sel_r[8] ? wbs_dat_o_mux_i[8] :
		      wb_slave_sel_r[9] ? wbs_dat_o_mux_i[9] :
		      wb_slave_sel_r[10] ? wbs_dat_o_mux_i[10] :
		      wb_slave_sel_r[11] ? wbs_dat_o_mux_i[11] :
		      wb_slave_sel_r[12] ? wbs_dat_o_mux_i[12] :
		      wb_slave_sel_r[13] ? wbs_dat_o_mux_i[13] :
		      wb_slave_sel_r[14] ? wbs_dat_o_mux_i[14] :
		      wb_slave_sel_r[15] ? wbs_dat_o_mux_i[15] :
		      wb_slave_sel_r[16] ? wbs_dat_o_mux_i[16] :
*/ 
		      wbs_dat_o_mux_i[0];
   // Master out acks, or together
   assign wbm_ack_i = wbs_ack_o_mux_i[0] |
		      wbs_ack_o_mux_i[1] /*|
		      wbs_ack_o_mux_i[2] |
		      wbs_ack_o_mux_i[3] |
		      wbs_ack_o_mux_i[4] |
		      wbs_ack_o_mux_i[5] |
		      wbs_ack_o_mux_i[6] |
		      wbs_ack_o_mux_i[7] |
		      wbs_ack_o_mux_i[8] |
		      wbs_ack_o_mux_i[9] |
		      wbs_ack_o_mux_i[10] |
		      wbs_ack_o_mux_i[11] |
		      wbs_ack_o_mux_i[12] |
		      wbs_ack_o_mux_i[13] |
		      wbs_ack_o_mux_i[14] |
		      wbs_ack_o_mux_i[15] |
		      wbs_ack_o_mux_i[16] */
		      ;
   

   assign wbm_err_i = wbs_err_o_mux_i[0] |
		      wbs_err_o_mux_i[1] |/*
		      wbs_err_o_mux_i[2] | 
		      wbs_err_o_mux_i[3] |
		      wbs_err_o_mux_i[4] |
		      wbs_err_o_mux_i[5] |
		      wbs_err_o_mux_i[6] |
		      wbs_err_o_mux_i[7] |
		      wbs_err_o_mux_i[8] |
		      wbs_err_o_mux_i[9] |
		      wbs_err_o_mux_i[10] |
		      wbs_err_o_mux_i[11] |
		      wbs_err_o_mux_i[12] |
		      wbs_err_o_mux_i[13] |
		      wbs_err_o_mux_i[14] |
		      wbs_err_o_mux_i[15] |
		      wbs_err_o_mux_i[16] |*/
		      watchdog_err  ;


   assign wbm_rty_i = wbs_rty_o_mux_i[0] |
		      wbs_rty_o_mux_i[1]/*|
		      wbs_rty_o_mux_i[2] |
		      wbs_rty_o_mux_i[3] |
		      wbs_rty_o_mux_i[4] |
		      wbs_rty_o_mux_i[5] |
		      wbs_rty_o_mux_i[6] |
		      wbs_rty_o_mux_i[7] |
		      wbs_rty_o_mux_i[8] |
		      wbs_rty_o_mux_i[9] |
		      wbs_rty_o_mux_i[10] |
		      wbs_rty_o_mux_i[11] |
		      wbs_rty_o_mux_i[12] |
		      wbs_rty_o_mux_i[13] |
		      wbs_rty_o_mux_i[14] |
		      wbs_rty_o_mux_i[15] |
		      wbs_rty_o_mux_i[16]*/;

endmodule // arbiter_dbus

