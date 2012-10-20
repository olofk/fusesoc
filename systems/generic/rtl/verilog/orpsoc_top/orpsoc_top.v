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
   wire [wb_aw-1:0] 	      wb_or1200_d_adr;
   wire [wb_dw-1:0] 	      wb_or1200_d_dat;
   wire [3:0] 		      wb_or1200_d_sel;
   wire 		      wb_or1200_d_we;
   wire 		      wb_or1200_d_cyc;
   wire 		      wb_or1200_d_stb;
   wire [2:0] 		      wb_or1200_d_cti;
   wire [1:0] 		      wb_or1200_d_bte;
   
   wire [wb_dw-1:0] 	      wb_or1200_d_sdt;   
   wire 		      wb_or1200_d_ack;
   wire 		      wb_or1200_d_err;
   wire 		      wb_or1200_d_rty;   

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
  
   wire [wb_dw-1:0] 	      wb_bbus_sdt;   
   wire 		      wb_bbus_ack;
   wire 		      wb_bbus_err;
   wire 		      wb_bbus_rty;   

   // Instruction bus slave wires //
   
   // rom0 instruction bus wires
   wire [31:0] wb_rom0_sdt;   
   wire        wb_rom0_ack;
   wire        wb_rom0_err;
   wire        wb_rom0_rty;   

   // mc0 instruction bus wires
   wire [31:0] wb_mc0_ibus_sdt;
   wire        wb_mc0_ibus_ack;
   wire        wb_mc0_ibus_err;
   wire        wb_mc0_ibus_rty;
   // mc0 data bus wires
   wire [31:0] wb_mc0_dbus_sdt;
   wire        wb_mc0_dbus_ack;
   wire        wb_mc0_dbus_err;
   wire        wb_mc0_dbus_rty;
   
   // Data bus slave wires //
   
   // mc0 data bus wires
   
   // uart0 wires
   wire [7:0]  wb_uart_sdt;   
   wire        wb_uart_ack;
   wire        wb_uart_err;
   wire        wb_uart_rty;   

      
   // intgen wires
   wire [7:0] 			     wb_intgen_sdt;
   wire 			     wb_intgen_ack;
   wire 			     wb_intgen_err;
   wire 			     wb_intgen_rty;

   wire [ibus_slaves-1:0] ibus_slave_sel =
	      {wb_or1200_i_adr[31:28] != 4'hf,
	       wb_or1200_i_adr[31:28] == 4'hf};
   

   wire [31:0] 		  wb_ibus_adr;
   wire [31:0] 		  wb_ibus_dat;
   wire [3:0] 		  wb_ibus_sel;
   wire 		  wb_ibus_we;
   wire [ibus_slaves-1:0] wb_ibus_cyc;
   wire [ibus_slaves-1:0] wb_ibus_stb;
   wire [2:0] 		  wb_ibus_cti;
   wire [1:0] 		  wb_ibus_bte;
   
   
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
      .wbs_adr_o   (wb_ibus_adr),
      .wbs_dat_o   (wb_ibus_dat),
      .wbs_sel_o   (wb_ibus_sel), 
      .wbs_we_o    (wb_ibus_we),
      .wbs_cyc_o   (wb_ibus_cyc),
      .wbs_stb_o   (wb_ibus_stb),
      .wbs_cti_o   (wb_ibus_cti),
      .wbs_bte_o   (wb_ibus_bte),
      .wbs_sdt_i   ({wb_mc0_ibus_sdt, wb_rom0_sdt}),
      .wbs_ack_i   ({wb_mc0_ibus_ack, wb_rom0_ack}),
      .wbs_err_i   ({wb_mc0_ibus_err, wb_rom0_err}),
      .wbs_rty_i   ({wb_mc0_ibus_rty, wb_rom0_rty}));
      
   wire [dbus_slaves-1:0] dbus_slave_sel =
			  {wb_or1200_d_adr[31:28] != 4'h0,
			   wb_or1200_d_adr[31:28] == 4'h0};

   wire [31:0] 		  wb_dbus_adr;
   wire [31:0] 		  wb_dbus_dat;
   wire [3:0] 		  wb_dbus_sel;
   wire 		  wb_dbus_we;
   wire [ibus_slaves-1:0] wb_dbus_cyc;
   wire [ibus_slaves-1:0] wb_dbus_stb;
   wire [2:0] 		  wb_dbus_cti;
   wire [1:0] 		  wb_dbus_bte;

   //
   // Wishbone data bus multiplexer
   //
   wb_mux wb_mux_dbus
     (.wb_clk      (wb_clk),
      .wb_rst      (wb_rst),
      .slave_sel_i (dbus_slave_sel),
      // Master Interface
      .wbm_adr_i   (wb_or1200_d_adr),
      .wbm_dat_i   (wb_or1200_d_dat),
      .wbm_sel_i   (wb_or1200_d_sel),
      .wbm_we_i    (wb_or1200_d_we),
      .wbm_cyc_i   (wb_or1200_d_cyc),
      .wbm_stb_i   (wb_or1200_d_stb),
      .wbm_cti_i   (wb_or1200_d_cti),
      .wbm_bte_i   (wb_or1200_d_bte),
      .wbm_sdt_o   (wb_or1200_d_sdt),
      .wbm_ack_o   (wb_or1200_d_ack),
      .wbm_err_o   (wb_or1200_d_err),
      .wbm_rty_o   (wb_or1200_d_rty), 
      //Slave interface
      .wbs_adr_o   (wb_dbus_adr),
      .wbs_dat_o   (wb_dbus_dat),
      .wbs_sel_o   (wb_dbus_sel), 
      .wbs_we_o    (wb_dbus_we),
      .wbs_cyc_o   (wb_dbus_cyc),
      .wbs_stb_o   (wb_dbus_stb),
      .wbs_cti_o   (wb_dbus_cti),
      .wbs_bte_o   (wb_dbus_bte),
      .wbs_sdt_i   ({wb_bbus_sdt, wb_mc0_dbus_sdt}),
      .wbs_ack_i   ({wb_bbus_ack, wb_mc0_dbus_ack}),
      .wbs_err_i   ({wb_bbus_err, wb_mc0_dbus_err}),
      .wbs_rty_i   ({wb_bbus_rty, wb_mc0_dbus_rty}));


   wire [bbus_slaves-1:0] bbus_slave_sel =
			  {wb_or1200_d_adr[31:24] == 8'he1,
			   wb_or1200_d_adr[31:24] == 8'h90};

   wire [31:0] 		  wb_bbus_adr;
   wire [7:0] 		  wb_bbus_dat;
   wire [3:0] 		  wb_bbus_sel;
   wire 		  wb_bbus_we;
   wire [ibus_slaves-1:0] wb_bbus_cyc;
   wire [ibus_slaves-1:0] wb_bbus_stb;
   wire [2:0] 		  wb_bbus_cti;
   wire [1:0] 		  wb_bbus_bte;

   //
   // Wishbone byte-wide bus arbiter
   //   
   wb_mux
     #(.sdw(8))
   wb_mux_bbus
     (.wb_clk      (wb_clk),
      .wb_rst      (wb_rst),
      .slave_sel_i (bbus_slave_sel),
      //Master interface
      .wbm_adr_i   (wb_dbus_adr),
      .wbm_dat_i   (wb_dbus_dat),
      .wbm_sel_i   (wb_dbus_sel),
      .wbm_we_i    (wb_dbus_we ),
      .wbm_cyc_i   (wb_dbus_cyc[bbus_slave_nr]),
      .wbm_stb_i   (wb_dbus_stb[bbus_slave_nr]),
      .wbm_cti_i   (wb_dbus_cti),
      .wbm_bte_i   (wb_dbus_bte),
      .wbm_sdt_o   (wb_bbus_sdt),
      .wbm_ack_o   (wb_bbus_ack),
      .wbm_err_o   (wb_bbus_err),
      .wbm_rty_o   (wb_bbus_rty),
      //Slave interface
      .wbs_adr_o   (wb_bbus_adr),
      .wbs_dat_o   (wb_bbus_dat),
      .wbs_we_o    (wb_bbus_we ),
      .wbs_cyc_o   (wb_bbus_cyc),
      .wbs_stb_o   (wb_bbus_stb),
      .wbs_cti_o   (wb_bbus_cti),
      .wbs_bte_o   (wb_bbus_bte),
      .wbs_sdt_i   ({wb_intgen_sdt, wb_uart_sdt}),
      .wbs_ack_i   ({wb_intgen_ack, wb_uart_ack}),
      .wbs_err_i   ({wb_intgen_err, wb_uart_err}),
      .wbs_rty_i   ({wb_intgen_rty, wb_uart_rty}));

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
	.dwb_ack_i			(wb_or1200_d_ack),
	.dwb_err_i			(wb_or1200_d_err),
	.dwb_rty_i			(wb_or1200_d_rty),
	.dwb_dat_i			(wb_or1200_d_sdt),

	.dwb_cyc_o			(wb_or1200_d_cyc),
	.dwb_adr_o			(wb_or1200_d_adr),
	.dwb_stb_o			(wb_or1200_d_stb),
	.dwb_we_o			(wb_or1200_d_we),
	.dwb_sel_o			(wb_or1200_d_sel),
	.dwb_dat_o			(wb_or1200_d_dat),
	.dwb_cti_o			(wb_or1200_d_cti),
	.dwb_bte_o			(wb_or1200_d_bte),
	
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
   rom
     #(.addr_width(rom0_aw))
   rom0
     (
      .wb_clk				(wb_clk),
      .wb_rst				(wb_rst),
      .wb_adr_i				(wb_ibus_adr[(rom0_aw+2)-1:2]),
      .wb_cyc_i				(wb_ibus_cyc[rom0_slave_nr]),
      .wb_stb_i				(wb_ibus_stb[rom0_slave_nr]),
      .wb_cti_i				(wb_ibus_cti),
      .wb_bte_i				(wb_ibus_bte),
      .wb_dat_o				(wb_rom0_sdt),
      .wb_ack_o				(wb_rom0_ack));
`else // !`ifdef BOOTROM
   assign wb_rom0_dat_o = 0;
   assign wb_rom0_ack_o = 0;
`endif // !`ifdef BOOTROM
   assign wb_rom0_err = 1'b0;
   assign wb_rom0_rty = 1'b0;

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
      .wbm0_dat_i			(wb_ibus_dat),
      .wbm0_adr_i			(wb_ibus_adr),
      .wbm0_sel_i			(wb_ibus_sel),
      .wbm0_cti_i			(wb_ibus_cti),
      .wbm0_bte_i			(wb_ibus_bte),
      .wbm0_we_i			(wb_ibus_we ),
      .wbm0_cyc_i			(wb_ibus_cyc[mc0_ibus_slave_nr]),
      .wbm0_stb_i			(wb_ibus_stb[mc0_ibus_slave_nr]),
      .wbm0_dat_o			(wb_mc0_ibus_sdt),
      .wbm0_ack_o			(wb_mc0_ibus_ack),
      .wbm0_err_o                       (wb_mc0_ibus_err),
      .wbm0_rty_o                       (wb_mc0_ibus_rty),
      // Wishbone slave interface 1
      .wbm1_dat_i			(wb_dbus_dat),
      .wbm1_adr_i			(wb_dbus_adr),
      .wbm1_sel_i			(wb_dbus_sel),
      .wbm1_cti_i			(wb_dbus_cti),
      .wbm1_bte_i			(wb_dbus_bte),
      .wbm1_we_i			(wb_dbus_we),
      .wbm1_cyc_i			(wb_dbus_cyc[mc0_dbus_slave_nr]),
      .wbm1_stb_i			(wb_dbus_stb[mc0_dbus_slave_nr]),
      .wbm1_dat_o			(wb_mc0_dbus_sdt),
      .wbm1_ack_o			(wb_mc0_dbus_ack),
      .wbm1_err_o                       (wb_mc0_dbus_err),
      .wbm1_rty_o                       (wb_mc0_dbus_rty),
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
   assign wb_uart_err = 0;
   assign wb_uart_rty = 0;
   
   uart_top uart16550_0
     (
      // Wishbone slave interface
      .wb_clk_i				(wb_clk),
      .wb_rst_i				(wb_rst),
      .wb_adr_i				(wb_bbus_adr[uart0_addr_width-1:0]),
      .wb_dat_i				(wb_bbus_dat),
      .wb_we_i				(wb_bbus_we),
      .wb_stb_i				(wb_bbus_stb[uart_slave_nr]),
      .wb_cyc_i				(wb_bbus_cyc[uart_slave_nr]),
      .wb_sel_i				(),
      .wb_dat_o				(wb_uart_sdt),
      .wb_ack_o				(wb_uart_ack),

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
   assign wb_uart_err = 0;   
   assign wb_uart_rty = 0;
   assign wb_uart_ack = 0;
   assign wb_uart_sdt = 0;
   
   ////////////////////////////////////////////////////////////////////////       
`endif // !`ifdef UART0

`ifdef INTGEN

   wire        intgen_irq;

   intgen intgen0
     (
      .clk_i                           (wb_clk),
      .rst_i                           (wb_rst),
      .wb_adr_i                        (wb_bbus_adr[intgen_addr_width-1:0]),
      .wb_dat_i                        (wb_bbus_dat),
      .wb_we_i                         (wb_bbus_we ),
      .wb_cyc_i                        (wb_bbus_cyc[intgen_slave_nr]),
      .wb_stb_i                        (wb_bbus_stb[intgen_slave_nr]),
      .wb_ack_o                        (wb_intgen_ack),
      .wb_dat_o                        (wb_intgen_sdt),
      
      .irq_o                           (intgen_irq)
      );

`endif //  `ifdef INTGEN
   assign wb_intgen_err = 0;
   assign wb_intgen_rty = 0;
   
   
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

