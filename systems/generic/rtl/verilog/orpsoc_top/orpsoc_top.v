//////////////////////////////////////////////////////////////////////
///                                                               //// 
/// ORPSoC top level                                              ////
///                                                               ////
/// Define I/O ports, instantiate modules                         ////
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

module orpsoc_top
  ( 
`ifdef JTAG_DEBUG    
    tdo_pad_o, tms_pad_i, tck_pad_i, tdi_pad_i,
`endif     
`ifdef UART0
    uart0_srx_pad_i, uart0_stx_pad_o, 
`endif
    clk_pad_i,
    rst_n_pad_i  
    );

`include "orpsoc-params.v"   

   input clk_pad_i;
   input rst_n_pad_i;
   
`ifdef JTAG_DEBUG    
   output tdo_pad_o;
   input  tms_pad_i;
   input  tck_pad_i;
   input  tdi_pad_i;
`endif
`ifdef UART0
   input  uart0_srx_pad_i;
   output uart0_stx_pad_o;
`endif
   parameter memory_file="";
   parameter IDCODE_VALUE=32'h14951185;
   ////////////////////////////////////////////////////////////////////////
   //
   // Clock and reset generation module
   // 
   ////////////////////////////////////////////////////////////////////////

   //
   // Wires
   //
   wire   async_rst;
   wire   wb_clk, wb_rst;
   wire   dbg_tck;

   
   clkgen clkgen0
     (

      .clk_pad_i             (clk_pad_i),

      .async_rst_o            (async_rst),
      
      .wb_clk_o                  (wb_clk),
      .wb_rst_o                  (wb_rst),

`ifdef JTAG_DEBUG
      .tck_pad_i                 (tck_pad_i),
      .dbg_tck_o                 (dbg_tck),
`endif      

      // Asynchronous active low reset
      .rst_n_pad_i               (rst_n_pad_i)
      );

   
   ////////////////////////////////////////////////////////////////////////
   //
   // Arbiter
   // 
   ////////////////////////////////////////////////////////////////////////
   
   // Wire naming convention:
   // First: wishbone master or slave (wbm/wbs)
   // Second: Which bus it's on instruction or data (i/d)
   // Third: Between which module and the arbiter the wires are
   // Fourth: Signal name
   // Fifth: Direction relative to module (not bus/arbiter!)
   //        ie. wbm_d_or12_adr_o is address OUT from the or1200

   // OR1200 instruction bus wires
   wire [wb_aw-1:0] 	      wb_or1200_i_adr;
   wire [wb_dw-1:0] 	      wb_or1200_i_dat;
   wire [3:0] 		      wb_or1200_i_sel;
   wire 		      wb_or1200_i_we;
   wire 		      wb_or1200_i_cyc;
   wire 		      wb_or1200_i_stb;
   wire [2:0] 		      wb_or1200_i_cti;
   wire [1:0] 		      wb_or1200_i_bte;
   
   wire [wb_dw-1:0] 	      wb_or1200_i_sdt;   
   wire 		      wb_or1200_i_ack;
   wire 		      wb_or1200_i_err;
   wire 		      wb_or1200_i_rty;

   // OR1200 data bus wires   
   wire [wb_aw-1:0] 	      wbm_d_or12_adr_o;
   wire [wb_dw-1:0] 	      wbm_d_or12_dat_o;
   wire [3:0] 		      wbm_d_or12_sel_o;
   wire 		      wbm_d_or12_we_o;
   wire 		      wbm_d_or12_cyc_o;
   wire 		      wbm_d_or12_stb_o;
   wire [2:0] 		      wbm_d_or12_cti_o;
   wire [1:0] 		      wbm_d_or12_bte_o;
   
   wire [wb_dw-1:0] 	      wbm_d_or12_dat_i;   
   wire 		      wbm_d_or12_ack_i;
   wire 		      wbm_d_or12_err_i;
   wire 		      wbm_d_or12_rty_i;   

   // Debug interface bus wires   
   wire [wb_aw-1:0] 	      wbm_d_dbg_adr_o;
   wire [wb_dw-1:0] 	      wbm_d_dbg_dat_o;
   wire [3:0] 		      wbm_d_dbg_sel_o;
   wire 		      wbm_d_dbg_we_o;
   wire 		      wbm_d_dbg_cyc_o;
   wire 		      wbm_d_dbg_stb_o;
   wire [2:0] 		      wbm_d_dbg_cti_o;
   wire [1:0] 		      wbm_d_dbg_bte_o;
   
   wire [wb_dw-1:0] 	      wbm_d_dbg_dat_i;   
   wire 		      wbm_d_dbg_ack_i;
   wire 		      wbm_d_dbg_err_i;
   wire 		      wbm_d_dbg_rty_i;

   // Byte bus bridge master signals
   wire [wb_aw-1:0] 	      wbm_b_d_adr_o;
   wire [wb_dw-1:0] 	      wbm_b_d_dat_o;
   wire [3:0] 		      wbm_b_d_sel_o;
   wire 		      wbm_b_d_we_o;
   wire 		      wbm_b_d_cyc_o;
   wire 		      wbm_b_d_stb_o;
   wire [2:0] 		      wbm_b_d_cti_o;
   wire [1:0] 		      wbm_b_d_bte_o;
   
   wire [wb_dw-1:0] 	      wbm_b_d_dat_i;   
   wire 		      wbm_b_d_ack_i;
   wire 		      wbm_b_d_err_i;
   wire 		      wbm_b_d_rty_i;   

   // Instruction bus slave wires //
   
   // rom0 instruction bus wires
   wire        wbs_rom0_cyc;
   wire        wbs_rom0_stb;

   wire [31:0] wbs_rom0_sdt;   
   wire        wbs_rom0_ack;
   wire        wbs_rom0_err;
   wire        wbs_rom0_rty;   

   // mc0 instruction bus wires
   wire 			    wbs_mc0_cyc;
   wire 			    wbs_mc0_stb;
   wire [31:0] 			    wbs_mc0_sdt;   
   wire 			    wbs_mc0_ack;
   wire 			    wbs_mc0_err;
   wire 			    wbs_mc0_rty;   
   
   // Data bus slave wires //
   
   // mc0 data bus wires
   wire [31:0] 			    wbs_d_mc0_adr_i;
   wire [31:0] 			    wbs_d_mc0_dat_i;
   wire [3:0] 			    wbs_d_mc0_sel_i;
   wire 			    wbs_d_mc0_we_i;
   wire 			    wbs_d_mc0_cyc_i;
   wire 			    wbs_d_mc0_stb_i;
   wire [2:0] 			    wbs_d_mc0_cti_i;
   wire [1:0] 			    wbs_d_mc0_bte_i;   
   wire [31:0] 			    wbs_d_mc0_dat_o;   
   wire 			    wbs_d_mc0_ack_o;
   wire 			    wbs_d_mc0_err_o;
   wire 			    wbs_d_mc0_rty_o;
   
   // uart0 wires
   wire [31:0] 			     wbs_d_uart0_adr_i;
   wire [wbs_d_uart0_data_width-1:0] wbs_d_uart0_dat_i;
   wire [3:0] 			     wbs_d_uart0_sel_i;
   wire 			     wbs_d_uart0_we_i;
   wire 			     wbs_d_uart0_cyc_i;
   wire 			     wbs_d_uart0_stb_i;
   wire [2:0] 			     wbs_d_uart0_cti_i;
   wire [1:0] 			     wbs_d_uart0_bte_i;   
   wire [wbs_d_uart0_data_width-1:0] wbs_d_uart0_dat_o;   
   wire 			     wbs_d_uart0_ack_o;
   wire 			     wbs_d_uart0_err_o;
   wire 			     wbs_d_uart0_rty_o;   

      
   // intgen wires
   wire [31:0] 			     wbs_d_intgen_adr_i;
   wire [7:0] 			     wbs_d_intgen_dat_i;
   wire [3:0] 			     wbs_d_intgen_sel_i;
   wire 			     wbs_d_intgen_we_i;
   wire 			     wbs_d_intgen_cyc_i;
   wire 			     wbs_d_intgen_stb_i;
   wire [2:0] 			     wbs_d_intgen_cti_i;
   wire [1:0] 			     wbs_d_intgen_bte_i;   
   wire [7:0] 			     wbs_d_intgen_dat_o;   
   wire 			     wbs_d_intgen_ack_o;
   wire 			     wbs_d_intgen_err_o;
   wire 			     wbs_d_intgen_rty_o;   

   wire [1:0] ibus_slave_sel =
	      {wb_or1200_i_adr[31:28] == 4'hf,
	       wb_or1200_i_adr[31:28] != 4'hf};
   

   wire [31:0] wbs_i_adr;
   wire [31:0] wbs_i_dat;
   wire [3:0]  wbs_i_sel;
   wire        wbs_i_we;
   wire        wbs_i_cyc;
   wire        wbs_i_stb;
   wire [2:0]  wbs_i_cti;
   wire [1:0]  wbs_i_bte;
   
   
   //
   // Wishbone instruction bus arbiter
   //
   wb_mux wb_mux_ibus
     (.wb_clk      (wb_clk),
      .wb_rst      (wb_rst),
      .slave_sel_i (ibus_slave_sel),
    // Master Interface
      .wbm_adr_i   (wb_or1200_i_adr),
      .wbm_dat_i   (wb_or1200_i_dat),
      .wbm_sel_i   (wb_or1200_i_sel),
      .wbm_we_i    (wb_or1200_i_we),
      .wbm_cyc_i   (wb_or1200_i_cyc),
      .wbm_stb_i   (wb_or1200_i_stb),
      .wbm_cti_i   (wb_or1200_i_cti),
      .wbm_bte_i   (wb_or1200_i_bte),
      .wbm_sdt_o   (wb_or1200_i_sdt),
      .wbm_ack_o   (wb_or1200_i_ack),
      .wbm_err_o   (wb_or1200_i_err),
      .wbm_rty_o   (wb_or1200_i_rty), 
      //Slave interface
      .wbs_adr_o   (wbs_i_adr),
      .wbs_dat_o   (wbs_i_dat),
      .wbs_sel_o   (wbs_i_sel), 
      .wbs_we_o    (wbs_i_we),
      .wbs_cyc_o   ({wbs_rom0_cyc, wbs_mc0_cyc}),
      .wbs_stb_o   ({wbs_rom0_stb, wbs_mc0_stb}),
      .wbs_cti_o   (wbs_i_cti),
      .wbs_bte_o   (wbs_i_bte),
      .wbs_sdt_i   ({wbs_rom0_sdt, wbs_mc0_sdt}),
      .wbs_ack_i   ({wbs_rom0_ack, wbs_mc0_ack}),
      .wbs_err_i   ({wbs_rom0_err, wbs_mc0_err}),
      .wbs_rty_i   ({wbs_rom0_rty, wbs_mc0_rty}));
      
   //
   // Wishbone data bus arbiter
   //
   
   arbiter_dbus arbiter_dbus0
     (
      // Master 0
      // Inputs to arbiter from master
      .wbm0_adr_o			(wbm_d_or12_adr_o),
      .wbm0_dat_o			(wbm_d_or12_dat_o),
      .wbm0_sel_o			(wbm_d_or12_sel_o),
      .wbm0_we_o			(wbm_d_or12_we_o),
      .wbm0_cyc_o			(wbm_d_or12_cyc_o),
      .wbm0_stb_o			(wbm_d_or12_stb_o),
      .wbm0_cti_o			(wbm_d_or12_cti_o),
      .wbm0_bte_o			(wbm_d_or12_bte_o),
      // Outputs to master from arbiter
      .wbm0_dat_i			(wbm_d_or12_dat_i),
      .wbm0_ack_i			(wbm_d_or12_ack_i),
      .wbm0_err_i			(wbm_d_or12_err_i),
      .wbm0_rty_i			(wbm_d_or12_rty_i),

      // Master 0
      // Inputs to arbiter from master
      .wbm1_adr_o			(wbm_d_dbg_adr_o),
      .wbm1_dat_o			(wbm_d_dbg_dat_o),
      .wbm1_we_o			(wbm_d_dbg_we_o),
      .wbm1_cyc_o			(wbm_d_dbg_cyc_o),
      .wbm1_sel_o			(wbm_d_dbg_sel_o),
      .wbm1_stb_o			(wbm_d_dbg_stb_o),
      .wbm1_cti_o			(wbm_d_dbg_cti_o),
      .wbm1_bte_o			(wbm_d_dbg_bte_o),
      // Outputs to master from arbiter      
      .wbm1_dat_i			(wbm_d_dbg_dat_i),
      .wbm1_ack_i			(wbm_d_dbg_ack_i),
      .wbm1_err_i			(wbm_d_dbg_err_i),
      .wbm1_rty_i			(wbm_d_dbg_rty_i),

      // Slaves
      
      .wbs0_adr_i			(wbs_d_mc0_adr_i),
      .wbs0_dat_i			(wbs_d_mc0_dat_i),
      .wbs0_sel_i			(wbs_d_mc0_sel_i),
      .wbs0_we_i			(wbs_d_mc0_we_i),
      .wbs0_cyc_i			(wbs_d_mc0_cyc_i),
      .wbs0_stb_i			(wbs_d_mc0_stb_i),
      .wbs0_cti_i			(wbs_d_mc0_cti_i),
      .wbs0_bte_i			(wbs_d_mc0_bte_i),
      .wbs0_dat_o			(wbs_d_mc0_dat_o),
      .wbs0_ack_o			(wbs_d_mc0_ack_o),
      .wbs0_err_o			(wbs_d_mc0_err_o),
      .wbs0_rty_o			(wbs_d_mc0_rty_o),

      .wbs1_adr_i			(wbm_b_d_adr_o),
      .wbs1_dat_i			(wbm_b_d_dat_o),
      .wbs1_sel_i			(wbm_b_d_sel_o),
      .wbs1_we_i			(wbm_b_d_we_o),
      .wbs1_cyc_i			(wbm_b_d_cyc_o),
      .wbs1_stb_i			(wbm_b_d_stb_o),
      .wbs1_cti_i			(wbm_b_d_cti_o),
      .wbs1_bte_i			(wbm_b_d_bte_o),
      .wbs1_dat_o			(wbm_b_d_dat_i),
      .wbs1_ack_o			(wbm_b_d_ack_i),
      .wbs1_err_o			(wbm_b_d_err_i),
      .wbs1_rty_o			(wbm_b_d_rty_i),

      // Clock, reset inputs
      .wb_clk			(wb_clk),
      .wb_rst			(wb_rst));

   // These settings are from top level params file
   defparam arbiter_dbus0.wb_addr_match_width = dbus_arb_wb_addr_match_width;
   defparam arbiter_dbus0.wb_num_slaves = dbus_arb_wb_num_slaves;
   defparam arbiter_dbus0.slave0_adr = dbus_arb_slave0_adr;
   defparam arbiter_dbus0.slave1_adr = dbus_arb_slave1_adr;

   //
   // Wishbone byte-wide bus arbiter
   //   
   
   arbiter_bytebus arbiter_bytebus0
     (

      // Master 0
      // Inputs to arbiter from master
      .wbm0_adr_o			(wbm_b_d_adr_o),
      .wbm0_dat_o			(wbm_b_d_dat_o),
      .wbm0_sel_o			(wbm_b_d_sel_o),
      .wbm0_we_o			(wbm_b_d_we_o),
      .wbm0_cyc_o			(wbm_b_d_cyc_o),
      .wbm0_stb_o			(wbm_b_d_stb_o),
      .wbm0_cti_o			(wbm_b_d_cti_o),
      .wbm0_bte_o			(wbm_b_d_bte_o),
      // Outputs to master from arbiter
      .wbm0_dat_i			(wbm_b_d_dat_i),
      .wbm0_ack_i			(wbm_b_d_ack_i),
      .wbm0_err_i			(wbm_b_d_err_i),
      .wbm0_rty_i			(wbm_b_d_rty_i),

      // Byte bus slaves
      
      .wbs0_adr_i			(wbs_d_uart0_adr_i),
      .wbs0_dat_i			(wbs_d_uart0_dat_i),
      .wbs0_we_i			(wbs_d_uart0_we_i),
      .wbs0_cyc_i			(wbs_d_uart0_cyc_i),
      .wbs0_stb_i			(wbs_d_uart0_stb_i),
      .wbs0_cti_i			(wbs_d_uart0_cti_i),
      .wbs0_bte_i			(wbs_d_uart0_bte_i),
      .wbs0_dat_o			(wbs_d_uart0_dat_o),
      .wbs0_ack_o			(wbs_d_uart0_ack_o),
      .wbs0_err_o			(wbs_d_uart0_err_o),
      .wbs0_rty_o			(wbs_d_uart0_rty_o),

      .wbs1_adr_i			(wbs_d_intgen_adr_i),
      .wbs1_dat_i			(wbs_d_intgen_dat_i),
      .wbs1_we_i			(wbs_d_intgen_we_i),
      .wbs1_cyc_i			(wbs_d_intgen_cyc_i),
      .wbs1_stb_i			(wbs_d_intgen_stb_i),
      .wbs1_cti_i			(wbs_d_intgen_cti_i),
      .wbs1_bte_i			(wbs_d_intgen_bte_i),
      .wbs1_dat_o			(wbs_d_intgen_dat_o),
      .wbs1_ack_o			(wbs_d_intgen_ack_o),
      .wbs1_err_o			(wbs_d_intgen_err_o),
      .wbs1_rty_o			(wbs_d_intgen_rty_o),

      // Clock, reset inputs
      .wb_clk			(wb_clk),
      .wb_rst			(wb_rst));

   defparam arbiter_bytebus0.wb_addr_match_width = bbus_arb_wb_addr_match_width;
   defparam arbiter_bytebus0.wb_num_slaves = bbus_arb_wb_num_slaves;

   defparam arbiter_bytebus0.slave0_adr = bbus_arb_slave0_adr;
   defparam arbiter_bytebus0.slave1_adr = bbus_arb_slave1_adr;

`ifdef JTAG_DEBUG   
   ////////////////////////////////////////////////////////////////////////
   //
   // JTAG TAP
   // 
   ////////////////////////////////////////////////////////////////////////

   //
   // Wires
   //
   wire 				  dbg_if_select;   
   wire 				  dbg_if_tdo;
   wire 				  jtag_tap_tdo;   
   wire 				  jtag_tap_shift_dr, jtag_tap_pause_dr, 
					  jtag_tap_update_dr, jtag_tap_capture_dr;
   //
   // Instantiation
   //

   tap_top #(.IDCODE_VALUE(IDCODE_VALUE)) jtag_tap0
     (
      // Ports to pads
      .tdo_pad_o			(tdo_pad_o),
      .tms_pad_i			(tms_pad_i),
      .tck_pad_i			(dbg_tck),
      .trst_pad_i			(async_rst),
      .tdi_pad_i			(tdi_pad_i),
      
      .tdo_padoe_o			(),
      
      .tdo_o				(jtag_tap_tdo),

      .shift_dr_o			(jtag_tap_shift_dr),
      .pause_dr_o			(jtag_tap_pause_dr),
      .update_dr_o			(jtag_tap_update_dr),
      .capture_dr_o			(jtag_tap_capture_dr),
      
      .extest_select_o			(),
      .sample_preload_select_o		(),
      .mbist_select_o			(),
      .debug_select_o			(dbg_if_select),

      
      .bs_chain_tdi_i			(1'b0),
      .mbist_tdi_i			(1'b0),
      .debug_tdi_i			(dbg_if_tdo)
      
      );
   
   ////////////////////////////////////////////////////////////////////////
`endif //  `ifdef JTAG_DEBUG

   ////////////////////////////////////////////////////////////////////////
   //
   // OpenRISC processor
   // 
   ////////////////////////////////////////////////////////////////////////

   // 
   // Wires
   // 
   
   wire [19:0] 				  or1200_pic_ints;

   wire [31:0] 				  or1200_dbg_dat_i;
   wire [31:0] 				  or1200_dbg_adr_i;
   wire 				  or1200_dbg_we_i;
   wire 				  or1200_dbg_stb_i;
   wire 				  or1200_dbg_ack_o;
   wire [31:0] 				  or1200_dbg_dat_o;
   
   wire 				  or1200_dbg_stall_i;
   wire 				  or1200_dbg_ewt_i;
   wire [3:0] 				  or1200_dbg_lss_o;
   wire [1:0] 				  or1200_dbg_is_o;
   wire [10:0] 				  or1200_dbg_wp_o;
   wire 				  or1200_dbg_bp_o;
   wire 				  or1200_dbg_rst;   
   
   wire 				  or1200_clk, or1200_rst;
   wire 				  sig_tick;
   
   //
   // Assigns
   //
   assign or1200_clk = wb_clk;
   assign or1200_rst = wb_rst | or1200_dbg_rst;

   // 
   // Instantiation
   //    
   or1200_top #(.boot_adr(32'hf0000000)) or1200_top0
       (
	// Instruction bus, clocks, reset
	.iwb_clk_i			(wb_clk),
	.iwb_rst_i			(wb_rst),
	.iwb_ack_i			(wb_or1200_i_ack),
	.iwb_err_i			(wb_or1200_i_err),
	.iwb_rty_i			(wb_or1200_i_rty),
	.iwb_dat_i			(wb_or1200_i_sdt),
	
	.iwb_cyc_o			(wb_or1200_i_cyc),
	.iwb_adr_o			(wb_or1200_i_adr),
	.iwb_stb_o			(wb_or1200_i_stb),
	.iwb_we_o			(wb_or1200_i_we),
	.iwb_sel_o			(wb_or1200_i_sel),
	.iwb_dat_o			(wb_or1200_i_dat),
	.iwb_cti_o			(wb_or1200_i_cti),
	.iwb_bte_o			(wb_or1200_i_bte),
	
	// Data bus, clocks, reset            
	.dwb_clk_i			(wb_clk),
	.dwb_rst_i			(wb_rst),
	.dwb_ack_i			(wbm_d_or12_ack_i),
	.dwb_err_i			(wbm_d_or12_err_i),
	.dwb_rty_i			(wbm_d_or12_rty_i),
	.dwb_dat_i			(wbm_d_or12_dat_i),

	.dwb_cyc_o			(wbm_d_or12_cyc_o),
	.dwb_adr_o			(wbm_d_or12_adr_o),
	.dwb_stb_o			(wbm_d_or12_stb_o),
	.dwb_we_o			(wbm_d_or12_we_o),
	.dwb_sel_o			(wbm_d_or12_sel_o),
	.dwb_dat_o			(wbm_d_or12_dat_o),
	.dwb_cti_o			(wbm_d_or12_cti_o),
	.dwb_bte_o			(wbm_d_or12_bte_o),
	
	// Debug interface ports
	.dbg_stall_i			(or1200_dbg_stall_i),
	//.dbg_ewt_i			(or1200_dbg_ewt_i),
	.dbg_ewt_i			(1'b0),
	.dbg_lss_o			(or1200_dbg_lss_o),
	.dbg_is_o			(or1200_dbg_is_o),
	.dbg_wp_o			(or1200_dbg_wp_o),
	.dbg_bp_o			(or1200_dbg_bp_o),

	.dbg_adr_i			(or1200_dbg_adr_i),      
	.dbg_we_i			(or1200_dbg_we_i ), 
	.dbg_stb_i			(or1200_dbg_stb_i),          
	.dbg_dat_i			(or1200_dbg_dat_i),
	.dbg_dat_o			(or1200_dbg_dat_o),
	.dbg_ack_o			(or1200_dbg_ack_o),
	
	.pm_clksd_o			(),
	.pm_dc_gate_o			(),
	.pm_ic_gate_o			(),
	.pm_dmmu_gate_o			(),
	.pm_immu_gate_o			(),
	.pm_tt_gate_o			(),
	.pm_cpu_gate_o			(),
	.pm_wakeup_o			(),
	.pm_lvolt_o			(),

	// Core clocks, resets
	.clk_i				(or1200_clk),
	.rst_i				(or1200_rst),
	
	.clmode_i			(2'b00),
	// Interrupts      
	.pic_ints_i			(or1200_pic_ints),
	.sig_tick(sig_tick),
	/*
	 .mbist_so_o			(),
	 .mbist_si_i			(0),
	 .mbist_ctrl_i			(0),
	 */

	.pm_cpustall_i			(1'b0)

	);
   
   ////////////////////////////////////////////////////////////////////////


`ifdef JTAG_DEBUG
   ////////////////////////////////////////////////////////////////////////
   //
   // OR1200 Debug Interface
   // 
   ////////////////////////////////////////////////////////////////////////
   
   dbg_top dbg_if0
     (
      // OR1200 interface
      .cpu0_clk_i			(or1200_clk),
      .cpu0_rst_o			(or1200_dbg_rst),      
      .cpu0_addr_o			(or1200_dbg_adr_i),
      .cpu0_data_o			(or1200_dbg_dat_i),
      .cpu0_stb_o			(or1200_dbg_stb_i),
      .cpu0_we_o			(or1200_dbg_we_i),
      .cpu0_data_i			(or1200_dbg_dat_o),
      .cpu0_ack_i			(or1200_dbg_ack_o),      


      .cpu0_stall_o			(or1200_dbg_stall_i),
      .cpu0_bp_i			(or1200_dbg_bp_o),      
      
      // TAP interface
      .tck_i				(dbg_tck),
      .tdi_i				(jtag_tap_tdo),
      .tdo_o				(dbg_if_tdo),      
      .rst_i				(wb_rst),
      .shift_dr_i			(jtag_tap_shift_dr),
      .pause_dr_i			(jtag_tap_pause_dr),
      .update_dr_i			(jtag_tap_update_dr),
      .debug_select_i			(dbg_if_select),

      // Wishbone debug master
      .wb_clk_i				(wb_clk),
      .wb_dat_i				(wbm_d_dbg_dat_i),
      .wb_ack_i				(wbm_d_dbg_ack_i),
      .wb_err_i				(wbm_d_dbg_err_i),
      .wb_adr_o				(wbm_d_dbg_adr_o),
      .wb_dat_o				(wbm_d_dbg_dat_o),
      .wb_cyc_o				(wbm_d_dbg_cyc_o),
      .wb_stb_o				(wbm_d_dbg_stb_o),
      .wb_sel_o				(wbm_d_dbg_sel_o),
      .wb_we_o				(wbm_d_dbg_we_o ),
      .wb_cti_o				(wbm_d_dbg_cti_o),
      .wb_cab_o                         (/*   UNUSED  */),
      .wb_bte_o				(wbm_d_dbg_bte_o)
      );
   
   ////////////////////////////////////////////////////////////////////////   
`else // !`ifdef JTAG_DEBUG

   assign wbm_d_dbg_adr_o = 0;   
   assign wbm_d_dbg_dat_o = 0;   
   assign wbm_d_dbg_cyc_o = 0;   
   assign wbm_d_dbg_stb_o = 0;   
   assign wbm_d_dbg_sel_o = 0;   
   assign wbm_d_dbg_we_o  = 0;   
   assign wbm_d_dbg_cti_o = 0;   
   assign wbm_d_dbg_bte_o = 0;  

   assign or1200_dbg_adr_i = 0;   
   assign or1200_dbg_dat_i = 0;   
   assign or1200_dbg_stb_i = 0;   
   assign or1200_dbg_we_i = 0;
   assign or1200_dbg_stall_i = 0;
   
   ////////////////////////////////////////////////////////////////////////   
`endif // !`ifdef JTAG_DEBUG
   

   ////////////////////////////////////////////////////////////////////////
   //
   // ROM
   // 
   ////////////////////////////////////////////////////////////////////////
`ifdef BOOTROM   
   rom rom0
     (
      .wb_dat_o				(wbs_rom0_sdt),
      .wb_ack_o				(wbs_rom0_ack),
      .wb_adr_i				(wbs_i_adr[(wbs_i_rom0_addr_width+2)-1:2]),
      .wb_stb_i				(wbs_rom0_stb),
      .wb_cyc_i				(wbs_rom0_cyc),
      .wb_cti_i				(wbs_i_cti),
      .wb_bte_i				(wbs_i_bte),
      .wb_clk				(wb_clk),
      .wb_rst				(wb_rst));

   defparam rom0.addr_width = wbs_i_rom0_addr_width;
   
   assign wbs_rom0_err = 1'b0;
   assign wbs_rom0_rty = 1'b0;
   
`else // !`ifdef BOOTROM
   assign wbs_i_rom0_dat_o = 0;
   assign wbs_i_rom0_ack_o = 0;
`endif // !`ifdef BOOTROM

   assign wbs_i_rom0_err_o = 0;
   assign wbs_i_rom0_rty_o = 0;
   
   ////////////////////////////////////////////////////////////////////////

`ifdef RAM_WB
   ////////////////////////////////////////////////////////////////////////
   //
   // Generic main RAM
   // 
   ////////////////////////////////////////////////////////////////////////


   ram_wb #(.memory_file(memory_file)) ram_wb0
     (
      // Wishbone slave interface 0
      .wbm0_dat_i			(wbs_i_dat),
      .wbm0_adr_i			(wbs_i_adr),
      .wbm0_sel_i			(wbs_i_sel),
      .wbm0_cti_i			(wbs_i_cti),
      .wbm0_bte_i			(wbs_i_bte),
      .wbm0_we_i			(wbs_i_we ),
      .wbm0_cyc_i			(wbs_mc0_cyc),
      .wbm0_stb_i			(wbs_mc0_stb),
      .wbm0_dat_o			(wbs_mc0_sdt),
      .wbm0_ack_o			(wbs_mc0_ack),
      .wbm0_err_o                       (wbs_mc0_err),
      .wbm0_rty_o                       (wbs_mc0_rty),
      // Wishbone slave interface 1
      .wbm1_dat_i			(wbs_d_mc0_dat_i),
      .wbm1_adr_i			(wbs_d_mc0_adr_i),
      .wbm1_sel_i			(wbs_d_mc0_sel_i),
      .wbm1_cti_i			(wbs_d_mc0_cti_i),
      .wbm1_bte_i			(wbs_d_mc0_bte_i),
      .wbm1_we_i			(wbs_d_mc0_we_i ),
      .wbm1_cyc_i			(wbs_d_mc0_cyc_i),
      .wbm1_stb_i			(wbs_d_mc0_stb_i),
      .wbm1_dat_o			(wbs_d_mc0_dat_o),
      .wbm1_ack_o			(wbs_d_mc0_ack_o),
      .wbm1_err_o                       (wbs_d_mc0_err_o),
      .wbm1_rty_o                       (wbs_d_mc0_rty_o),
      // Wishbone slave interface 2
      .wbm2_dat_i			(32'd0),
      .wbm2_adr_i			(32'd0),
      .wbm2_sel_i			(4'd0),
      .wbm2_cti_i			(3'd0),
      .wbm2_bte_i			(2'd0),
      .wbm2_we_i			(1'd0),
      .wbm2_cyc_i			(1'd0),
      .wbm2_stb_i			(1'd0),
      .wbm2_dat_o			(),
      .wbm2_ack_o			(),
      .wbm2_err_o                       (),
      .wbm2_rty_o                       (),
      // Clock, reset
      .wb_clk_i				(wb_clk),
      .wb_rst_i				(wb_rst));

   defparam ram_wb0.aw = wb_aw;
   defparam ram_wb0.dw = wb_dw;

   defparam ram_wb0.mem_size_bytes = (8192*1024); // 8MB
   defparam ram_wb0.mem_adr_width = 23; // log2(8192*1024)
   
   
   ////////////////////////////////////////////////////////////////////////
`endif   
`ifdef UART0
   ////////////////////////////////////////////////////////////////////////
   //
   // UART0
   // 
   ////////////////////////////////////////////////////////////////////////

   //
   // Wires
   //
   wire        uart0_irq;

   //
   // Assigns
   //
   assign wbs_d_uart0_err_o = 0;
   assign wbs_d_uart0_rty_o = 0;
   
   uart_top uart16550_0
     (
      // Wishbone slave interface
      .wb_clk_i				(wb_clk),
      .wb_rst_i				(wb_rst),
      .wb_adr_i				(wbs_d_uart0_adr_i[uart0_addr_width-1:0]),
      .wb_dat_i				(wbs_d_uart0_dat_i),
      .wb_we_i				(wbs_d_uart0_we_i),
      .wb_stb_i				(wbs_d_uart0_stb_i),
      .wb_cyc_i				(wbs_d_uart0_cyc_i),
      .wb_sel_i				(),
      .wb_dat_o				(wbs_d_uart0_dat_o),
      .wb_ack_o				(wbs_d_uart0_ack_o),

      .int_o				(uart0_irq),
      .stx_pad_o			(uart0_stx_pad_o),
      .rts_pad_o			(),
      .dtr_pad_o			(),
      //      .baud_o				(),
      // Inputs
      .srx_pad_i			(uart0_srx_pad_i),
      .cts_pad_i			(1'b0),
      .dsr_pad_i			(1'b0),
      .ri_pad_i				(1'b0),
      .dcd_pad_i			(1'b0));

   ////////////////////////////////////////////////////////////////////////          
`else // !`ifdef UART0
   
   //
   // Assigns
   //
   assign wbs_d_uart0_err_o = 0;   
   assign wbs_d_uart0_rty_o = 0;
   assign wbs_d_uart0_ack_o = 0;
   assign wbs_d_uart0_dat_o = 0;
   
   ////////////////////////////////////////////////////////////////////////       
`endif // !`ifdef UART0

`ifdef INTGEN

   wire        intgen_irq;

   intgen intgen0
     (
      .clk_i                           (wb_clk),
      .rst_i                           (wb_rst),
      .wb_adr_i                        (wbs_d_intgen_adr_i[intgen_addr_width-1:0]),
      .wb_cyc_i                        (wbs_d_intgen_cyc_i),
      .wb_stb_i                        (wbs_d_intgen_stb_i),
      .wb_dat_i                        (wbs_d_intgen_dat_i),
      .wb_we_i                         (wbs_d_intgen_we_i),
      .wb_ack_o                        (wbs_d_intgen_ack_o),
      .wb_dat_o                        (wbs_d_intgen_dat_o),
      
      .irq_o                           (intgen_irq)
      );

`endif //  `ifdef INTGEN
   assign wbs_d_intgen_err_o = 0;
   assign wbs_d_intgen_rty_o = 0;
   
   
   ////////////////////////////////////////////////////////////////////////
   //
   // OR1200 Interrupt assignment
   // 
   ////////////////////////////////////////////////////////////////////////
   
   assign or1200_pic_ints[0] = 0; // Non-maskable inside OR1200
   assign or1200_pic_ints[1] = 0; // Non-maskable inside OR1200
`ifdef UART0
   assign or1200_pic_ints[2] = uart0_irq;
`else   
   assign or1200_pic_ints[2] = 0;
`endif
   assign or1200_pic_ints[3] = 0;
   assign or1200_pic_ints[4] = 0;
   assign or1200_pic_ints[5] = 0;
`ifdef SPI0
   assign or1200_pic_ints[6] = spi0_irq;
`else   
   assign or1200_pic_ints[6] = 0;
`endif
   assign or1200_pic_ints[7] = 0;
   assign or1200_pic_ints[8] = 0;
   assign or1200_pic_ints[9] = 0;
   assign or1200_pic_ints[10] = 0;
   assign or1200_pic_ints[11] = 0;
   assign or1200_pic_ints[12] = 0;
   assign or1200_pic_ints[13] = 0;
   assign or1200_pic_ints[14] = 0;
   assign or1200_pic_ints[15] = 0;
   assign or1200_pic_ints[16] = 0;
   assign or1200_pic_ints[17] = 0;
   assign or1200_pic_ints[18] = 0;
`ifdef INTGEN
   assign or1200_pic_ints[19] = intgen_irq;
`else
   assign or1200_pic_ints[19] = 0;
`endif
   
endmodule // top

// Local Variables:
// verilog-library-directories:("." "../arbiter" "../uart16550" "../or1200" "../dbg_if" "../jtag_tap" "../rom" "../simple_spi" )
// verilog-library-files:()
// verilog-library-extensions:(".v" ".h")
// End:

