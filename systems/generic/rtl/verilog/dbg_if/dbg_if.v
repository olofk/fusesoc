//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_top.v                                                   ////
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
// $Log: dbg_top.v,v $
// Revision 1.45  2004/04/01 11:56:59  igorm
// Port names and defines for the supported CPUs changed.
//
// Revision 1.44  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.43  2004/03/22 16:35:46  igorm
// Temp version before changing dbg interface.
//
// Revision 1.42  2004/01/30 10:24:31  mohor
// Defines WISHBONE_SUPPORTED and CPU_SUPPORTED added. By default both are
// turned on.
//
// Revision 1.41  2004/01/25 14:04:18  mohor
// All flipflops are reset.
//
// Revision 1.40  2004/01/20 14:23:47  mohor
// Define name changed.
//
// Revision 1.39  2004/01/19 07:32:41  simons
// Reset values width added because of FV, a good sentence changed because some tools can not handle it.
//
// Revision 1.38  2004/01/18 09:22:47  simons
// Sensitivity list updated.
//
// Revision 1.37  2004/01/17 17:01:14  mohor
// Almost finished.
//
// Revision 1.36  2004/01/16 14:51:33  mohor
// cpu registers added.
//
// Revision 1.35  2004/01/14 22:59:16  mohor
// Temp version.
//
// Revision 1.34  2003/12/23 15:07:34  mohor
// New directory structure. New version of the debug interface.
// Files that are not needed removed.
//
// Revision 1.33  2003/10/23 16:17:01  mohor
// CRC logic changed.
//
// Revision 1.32  2003/09/18 14:00:47  simons
// Lower two address lines must be always zero.
//
// Revision 1.31  2003/09/17 14:38:57  simons
// WB_CNTL register added, some syncronization fixes.
//
// Revision 1.30  2003/08/28 13:55:22  simons
// Three more chains added for cpu debug access.
//
// Revision 1.29  2003/07/31 12:19:49  simons
// Multiple cpu support added.
//
// Revision 1.28  2002/11/06 14:22:41  mohor
// Trst signal is not inverted here any more. Inverted on higher layer !!!.
//
// Revision 1.27  2002/10/10 02:42:55  mohor
// WISHBONE Scan Chain is changed to reflect state of the WISHBONE access (WBInProgress bit added). 
// Internal counter is used (counts 256 wb_clk cycles) and when counter exceeds that value, 
// wb_cyc_o is negated.
//
// Revision 1.26  2002/05/07 14:43:59  mohor
// mon_cntl_o signals that controls monitor mux added.
//
// Revision 1.25  2002/04/22 12:54:11  mohor
// Signal names changed to lower case.
//
// Revision 1.24  2002/04/17 13:17:01  mohor
// Intentional error removed.
//
// Revision 1.23  2002/04/17 11:16:33  mohor
// A block for checking possible simulation/synthesis missmatch added.
//
// Revision 1.22  2002/03/12 10:31:53  mohor
// tap_top and dbg_top modules are put into two separate modules. tap_top
// contains only tap state machine and related logic. dbg_top contains all
// logic necessery for debugging.
//
// Revision 1.21  2002/03/08 15:28:16  mohor
// Structure changed. Hooks for jtag chain added.
//
// Revision 1.20  2002/02/06 12:23:09  mohor
// latched_jtag_ir used when muxing TDO instead of JTAG_IR.
//
// Revision 1.19  2002/02/05 13:34:51  mohor
// Stupid bug that was entered by previous update fixed.
//
// Revision 1.18  2002/02/05 12:41:01  mohor
// trst synchronization is not needed and was removed.
//
// Revision 1.17  2002/01/25 07:58:35  mohor
// IDCODE bug fixed, chains reused to decreas size of core. Data is shifted-in
// not filled-in. Tested in hw.
//
// Revision 1.16  2001/12/20 11:17:26  mohor
// TDO and TDO Enable signal are separated into two signals.
//
// Revision 1.15  2001/12/05 13:28:21  mohor
// trst signal is synchronized to wb_clk_i.
//
// Revision 1.14  2001/11/28 09:36:15  mohor
// Register length fixed.
//
// Revision 1.13  2001/11/27 13:37:43  mohor
// CRC is returned when chain selection data is transmitted.
//
// Revision 1.12  2001/11/26 10:47:09  mohor
// Crc generation is different for read or write commands. Small synthesys fixes.
//
// Revision 1.11  2001/11/14 10:10:41  mohor
// Wishbone data latched on wb_clk_i instead of risc_clk.
//
// Revision 1.10  2001/11/12 01:11:27  mohor
// Reset signals are not combined any more.
//
// Revision 1.9  2001/10/19 11:40:01  mohor
// dbg_timescale.v changed to timescale.v This is done for the simulation of
// few different cores in a single project.
//
// Revision 1.8  2001/10/17 10:39:03  mohor
// bs_chain_o added.
//
// Revision 1.7  2001/10/16 10:09:56  mohor
// Signal names changed to lowercase.
//
//
// Revision 1.6  2001/10/15 09:55:47  mohor
// Wishbone interface added, few fixes for better performance,
// hooks for boundary scan testing added.
//
// Revision 1.5  2001/09/24 14:06:42  mohor
// Changes connected to the OpenRISC access (SPR read, SPR write).
//
// Revision 1.4  2001/09/20 10:11:25  mohor
// Working version. Few bugs fixed, comments added.
//
// Revision 1.3  2001/09/19 11:55:13  mohor
// Asynchronous set/reset not used in trace any more.
//
// Revision 1.2  2001/09/18 14:13:47  mohor
// Trace fixed. Some registers changed, trace simplified.
//
// Revision 1.1.1.1  2001/09/13 13:49:19  mohor
// Initial official release.
//
// Revision 1.3  2001/06/01 22:22:35  mohor
// This is a backup. It is not a fully working version. Not for use, yet.
//
// Revision 1.2  2001/05/18 13:10:00  mohor
// Headers changed. All additional information is now avaliable in the README.txt file.
//
// Revision 1.1.1.1  2001/05/18 06:35:02  mohor
// Initial release
//
//

// synopsys translate_off
`include "timescale.v"
// synopsys translate_on
`include "dbg_defines.v"
`include "dbg_cpu_defines.v"

// Top module
//module dbg_top(
module dbg_if( // Renamed by julius
                // JTAG signals
                tck_i,
                tdi_i,
                tdo_o,
                rst_i,

                // TAP states
                shift_dr_i,
                pause_dr_i,
                update_dr_i,

                // Instructions
                debug_select_i


                `ifdef DBG_WISHBONE_SUPPORTED
                // WISHBONE common signals
                ,
                wb_clk_i,
                                                                                
                // WISHBONE master interface
                wb_adr_o,
                wb_dat_o,
                wb_dat_i,
                wb_cyc_o,
                wb_stb_o,
                wb_sel_o,
                wb_we_o,
                wb_ack_i,
                wb_cab_o,
                wb_err_i,
                wb_cti_o,
                wb_bte_o
                `endif

                `ifdef DBG_CPU0_SUPPORTED
                // CPU signals
                ,
                cpu0_clk_i, 
                cpu0_addr_o, 
                cpu0_data_i, 
                cpu0_data_o,
                cpu0_bp_i,
                cpu0_stall_o,
                cpu0_stb_o,
                cpu0_we_o,
                cpu0_ack_i,
                cpu0_rst_o
                `endif

                `ifdef DBG_CPU1_SUPPORTED
                // CPU signals
                ,
                cpu1_clk_i, 
                cpu1_addr_o, 
                cpu1_data_i, 
                cpu1_data_o,
                cpu1_bp_i,
                cpu1_stall_o,
                cpu1_stb_o,
                cpu1_we_o,
                cpu1_ack_i,
                cpu1_rst_o
                `endif

              );


// JTAG signals
input   tck_i;
input   tdi_i;
output  tdo_o;
input   rst_i;

// TAP states
input   shift_dr_i;
input   pause_dr_i;
input   update_dr_i;

// Instructions
input   debug_select_i;

`ifdef DBG_WISHBONE_SUPPORTED
input         wb_clk_i;
output [31:0] wb_adr_o;
output [31:0] wb_dat_o;
input  [31:0] wb_dat_i;
output        wb_cyc_o;
output        wb_stb_o;
output  [3:0] wb_sel_o;
output        wb_we_o;
input         wb_ack_i;
output        wb_cab_o;
input         wb_err_i;
output  [2:0] wb_cti_o;
output  [1:0] wb_bte_o;

reg           wishbone_module;
reg           wishbone_ce;
wire          tdi_wb;
wire          tdo_wb;
wire          crc_en_wb;
wire          shift_crc_wb;
`else
wire          crc_en_wb = 1'b0;
wire          shift_crc_wb = 1'b0;
`endif

`ifdef DBG_CPU0_SUPPORTED
// CPU signals
input         cpu0_clk_i; 
output [31:0] cpu0_addr_o; 
input  [31:0] cpu0_data_i; 
output [31:0] cpu0_data_o;
input         cpu0_bp_i;
output        cpu0_stall_o;
output        cpu0_stb_o;
output        cpu0_we_o;
input         cpu0_ack_i;
output        cpu0_rst_o;

reg           cpu0_debug_module;
reg           cpu0_ce;
wire          cpu0_tdi;
wire          cpu0_tdo;
wire          cpu0_crc_en;
wire          cpu0_shift_crc;
`else
wire          cpu0_crc_en = 1'b0;
wire          cpu0_shift_crc = 1'b0;
`endif

`ifdef DBG_CPU1_SUPPORTED
input         cpu1_clk_i; 
output [31:0] cpu1_addr_o; 
input  [31:0] cpu1_data_i; 
output [31:0] cpu1_data_o;
input         cpu1_bp_i;
output        cpu1_stall_o;
output        cpu1_stb_o;
output        cpu1_we_o;
input         cpu1_ack_i;
output        cpu1_rst_o;

reg           cpu1_debug_module;
reg           cpu1_ce;
wire          cpu1_tdi;
wire          cpu1_tdo;
wire          cpu1_crc_en;
wire          cpu1_shift_crc;
`else
wire          cpu1_crc_en = 1'b0;
wire          cpu1_shift_crc = 1'b0;
`endif


reg [`DBG_TOP_DATA_CNT -1:0]        data_cnt;
reg [`DBG_TOP_CRC_CNT -1:0]         crc_cnt;
reg [`DBG_TOP_STATUS_CNT_WIDTH -1:0]      status_cnt;
reg [`DBG_TOP_MODULE_DATA_LEN -1:0]  module_dr;
reg [`DBG_TOP_MODULE_ID_LENGTH -1:0] module_id; 

wire module_latch_en;
wire data_cnt_end;
wire crc_cnt_end;
wire status_cnt_end;
reg  crc_cnt_end_q;
reg  module_select;
reg  module_select_error;
wire crc_out;
wire crc_match;

wire data_shift_en;
wire selecting_command;

reg tdo_o;




wire shift_crc;

// data counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    data_cnt <=  {`DBG_TOP_DATA_CNT{1'b0}};
  else if(shift_dr_i & (~data_cnt_end))
    data_cnt <=  data_cnt + 1;
  else if (update_dr_i)
    data_cnt <=  {`DBG_TOP_DATA_CNT{1'b0}};
end


assign data_cnt_end = data_cnt == `DBG_TOP_MODULE_DATA_LEN;


// crc counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    crc_cnt <=  {`DBG_TOP_CRC_CNT{1'b0}};
  else if(shift_dr_i & data_cnt_end & (~crc_cnt_end) & module_select)
    crc_cnt <=  crc_cnt + 1;
  else if (update_dr_i)
    crc_cnt <=  {`DBG_TOP_CRC_CNT{1'b0}};
end

assign crc_cnt_end = crc_cnt == `DBG_TOP_CRC_LEN;


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    crc_cnt_end_q  <=  1'b0;
  else
    crc_cnt_end_q  <=  crc_cnt_end;
end


// status counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    status_cnt <=  {`DBG_TOP_STATUS_CNT_WIDTH{1'b0}};
  else if(shift_dr_i & crc_cnt_end & (~status_cnt_end))
    status_cnt <=  status_cnt + 1;
  else if (update_dr_i)
    status_cnt <=  {`DBG_TOP_STATUS_CNT_WIDTH{1'b0}};
end

assign status_cnt_end = status_cnt == `DBG_TOP_STATUS_LEN;


assign selecting_command = shift_dr_i & (data_cnt == `DBG_TOP_DATA_CNT'h0) & debug_select_i;


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    module_select <=  1'b0;
  else if(selecting_command & tdi_i)       // Chain select
    module_select <=  1'b1;
  else if (update_dr_i)
    module_select <=  1'b0;
end

/* verilator lint_off COMBDLY */
always @ (module_id)
begin
  `ifdef DBG_CPU0_SUPPORTED
  cpu0_debug_module  <=  1'b0;
  `endif
  `ifdef DBG_CPU1_SUPPORTED
  cpu1_debug_module  <=  1'b0;
  `endif
  `ifdef DBG_WISHBONE_SUPPORTED
  wishbone_module   <=  1'b0;
  `endif
  module_select_error    <=  1'b0;
  
  case (module_id)                /* synthesis parallel_case */
    `ifdef DBG_CPU0_SUPPORTED
      `DBG_TOP_CPU0_DEBUG_MODULE     :   cpu0_debug_module   <=  1'b1;
    `endif
    `ifdef DBG_CPU1_SUPPORTED
      `DBG_TOP_CPU1_DEBUG_MODULE     :   cpu1_debug_module   <=  1'b1;
    `endif
    `ifdef DBG_WISHBONE_SUPPORTED
      `DBG_TOP_WISHBONE_DEBUG_MODULE :   wishbone_module     <=  1'b1;
    `endif
    default                          :   module_select_error <=  1'b1; 
  endcase
end
/* verilator lint_on COMBDLY */

assign module_latch_en = module_select & crc_cnt_end & (~crc_cnt_end_q);


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    module_id <= {`DBG_TOP_MODULE_ID_LENGTH{1'b1}};
  else if(module_latch_en & crc_match)
    module_id <=  module_dr[`DBG_TOP_MODULE_DATA_LEN -2:0];
end


assign data_shift_en = shift_dr_i & (~data_cnt_end);


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    module_dr <=  0;   
  else if (data_shift_en)
    module_dr[`DBG_TOP_MODULE_DATA_LEN -1:0] <=  {module_dr[`DBG_TOP_MODULE_DATA_LEN -2:0], tdi_i};
end


// Calculating crc for input data
dbg_crc32_d1 i_dbg_crc32_d1_in
             ( 
              .data       (tdi_i),
              .enable     (shift_dr_i),
              .shift      (1'b0),
              .rst        (rst_i),
              .sync_rst   (update_dr_i),
              .crc_out    (),
              .clk        (tck_i),
              .crc_match  (crc_match)
             );


reg tdo_module_select;
wire crc_en;
wire crc_en_dbg;
reg crc_started;

assign crc_en = crc_en_dbg | crc_en_wb | cpu1_crc_en | cpu0_crc_en;

assign crc_en_dbg = shift_dr_i & crc_cnt_end & (~status_cnt_end);

always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    crc_started <=  1'b0;
  else if (crc_en)
    crc_started <=  1'b1;
  else if (update_dr_i)
    crc_started <=  1'b0;
end


reg tdo_tmp;


// Calculating crc for input data
dbg_crc32_d1 i_dbg_crc32_d1_out
             ( 
              .data       (tdo_tmp),
              .enable     (crc_en), // enable has priority
//              .shift      (1'b0),
              .shift      (shift_dr_i & crc_started & (~crc_en)),
              .rst        (rst_i),
              .sync_rst   (update_dr_i),
              .crc_out    (crc_out),
              .clk        (tck_i),
              .crc_match  ()
             );

// Following status is shifted out: 
// 1. bit:          0 if crc is OK, else 1
// 2. bit:          0 if existing module_id is selected, 1 if non-existing module_id is selected
// 3. bit:          0 (always) 
// 4. bit:          0 (always)


always @ (status_cnt or crc_match or module_select_error or crc_out)
begin
  case (status_cnt)                   /* synthesis full_case parallel_case */ 
    `DBG_TOP_STATUS_CNT_WIDTH'd0  : begin
                        tdo_module_select = ~crc_match;
                      end
    `DBG_TOP_STATUS_CNT_WIDTH'd1  : begin
                        tdo_module_select = module_select_error;
                      end
    `DBG_TOP_STATUS_CNT_WIDTH'd2  : begin
                        tdo_module_select = 1'b0;
                      end
    `DBG_TOP_STATUS_CNT_WIDTH'd3  : begin
                        tdo_module_select = 1'b0;
                      end
    `DBG_TOP_STATUS_CNT_WIDTH'd4  : begin
                        tdo_module_select = crc_out;
                      end
     default : begin    tdo_module_select = 1'b0; end			//me added
  endcase
end




assign shift_crc = shift_crc_wb | cpu1_shift_crc | cpu0_shift_crc;

always @ (shift_crc or crc_out or tdo_module_select
`ifdef DBG_WISHBONE_SUPPORTED
 or wishbone_ce or tdo_wb
`endif
`ifdef DBG_CPU0_SUPPORTED
 or cpu0_ce or cpu0_tdo
`endif
`ifdef DBG_CPU1_SUPPORTED
 or cpu1_ce or cpu1_tdo
`endif
         )
begin
  if (shift_crc)          // shifting crc
    tdo_tmp = crc_out;
  `ifdef DBG_WISHBONE_SUPPORTED
  else if (wishbone_ce)   //  shifting data from wb
    tdo_tmp = tdo_wb;
  `endif
  `ifdef DBG_CPU0_SUPPORTED
  else if (cpu0_ce)        // shifting data from cpu
    tdo_tmp = cpu0_tdo;
  `endif
  `ifdef DBG_CPU1_SUPPORTED
  else if (cpu1_ce)        // shifting data from cpu
    tdo_tmp = cpu1_tdo;
  `endif
  else
    tdo_tmp = tdo_module_select;
end


always @ (negedge tck_i)
begin
  tdo_o <=  tdo_tmp;
end




// Signals for WISHBONE module


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      `ifdef DBG_WISHBONE_SUPPORTED
      wishbone_ce <=  1'b0;
      `endif
      `ifdef DBG_CPU0_SUPPORTED
      cpu0_ce <=  1'b0;
      `endif
      `ifdef DBG_CPU1_SUPPORTED
      cpu1_ce <=  1'b0;
      `endif
    end
  else if(selecting_command & (~tdi_i))
    begin
      `ifdef DBG_WISHBONE_SUPPORTED
      if (wishbone_module)      // wishbone CE
        wishbone_ce <=  1'b1;
      `endif
      `ifdef DBG_CPU0_SUPPORTED
      if (cpu0_debug_module)     // CPU CE
        cpu0_ce <=  1'b1;
      `endif
      `ifdef DBG_CPU1_SUPPORTED
      if (cpu1_debug_module)     // CPU CE
        cpu1_ce <=  1'b1;
      `endif
    end
  else if (update_dr_i)
    begin
      `ifdef DBG_WISHBONE_SUPPORTED
      wishbone_ce <=  1'b0;
      `endif
      `ifdef DBG_CPU0_SUPPORTED
      cpu0_ce <=  1'b0;
      `endif
      `ifdef DBG_CPU1_SUPPORTED
      cpu1_ce <=  1'b0;
      `endif
    end
end


`ifdef DBG_WISHBONE_SUPPORTED
assign tdi_wb  = wishbone_ce & tdi_i;
`endif

`ifdef DBG_CPU0_SUPPORTED
assign cpu0_tdi = cpu0_ce & tdi_i;
`endif
`ifdef DBG_CPU1_SUPPORTED
assign cpu1_tdi = cpu1_ce & tdi_i;
`endif


`ifdef DBG_WISHBONE_SUPPORTED
// Connecting wishbone module
dbg_wb i_dbg_wb (
                  // JTAG signals
                  .tck_i            (tck_i),
                  .tdi_i            (tdi_wb),
                  .tdo_o            (tdo_wb),

                  // TAP states
                  .shift_dr_i       (shift_dr_i),
                  .pause_dr_i       (pause_dr_i),
                  .update_dr_i      (update_dr_i),

                  .wishbone_ce_i    (wishbone_ce),
                  .crc_match_i      (crc_match),
                  .crc_en_o         (crc_en_wb),
                  .shift_crc_o      (shift_crc_wb),
                  .rst_i            (rst_i),

                  // WISHBONE common signals
                  .wb_clk_i         (wb_clk_i),

                  // WISHBONE master interface
                  .wb_adr_o         (wb_adr_o), 
                  .wb_dat_o         (wb_dat_o),
                  .wb_dat_i         (wb_dat_i),
                  .wb_cyc_o         (wb_cyc_o),
                  .wb_stb_o         (wb_stb_o),
                  .wb_sel_o         (wb_sel_o),
                  .wb_we_o          (wb_we_o),
                  .wb_ack_i         (wb_ack_i),
                  .wb_cab_o         (wb_cab_o),
                  .wb_err_i         (wb_err_i),
                  .wb_cti_o         (wb_cti_o),
                  .wb_bte_o         (wb_bte_o)
            );
`endif



`ifdef DBG_CPU0_SUPPORTED
dbg_cpu i_dbg_cpu_or1k (
                  // JTAG signals
                  .tck_i            (tck_i),
                  .tdi_i            (cpu0_tdi),
                  .tdo_o            (cpu0_tdo),

                  // TAP states
                  .shift_dr_i       (shift_dr_i),
                  .pause_dr_i       (pause_dr_i),
                  .update_dr_i      (update_dr_i),

                  .cpu_ce_i         (cpu0_ce),
                  .crc_match_i      (crc_match),
                  .crc_en_o         (cpu0_crc_en),
                  .shift_crc_o      (cpu0_shift_crc),
                  .rst_i            (rst_i),

                  // CPU signals
                  .cpu_clk_i        (cpu0_clk_i), 
                  .cpu_addr_o       (cpu0_addr_o), 
                  .cpu_data_i       (cpu0_data_i), 
                  .cpu_data_o       (cpu0_data_o),
                  .cpu_bp_i         (cpu0_bp_i),
                  .cpu_stall_o      (cpu0_stall_o),
                  .cpu_stb_o        (cpu0_stb_o),
                  .cpu_we_o         (cpu0_we_o),
                  .cpu_ack_i        (cpu0_ack_i),
                  .cpu_rst_o        (cpu0_rst_o)
              );

`endif  //  DBG_CPU0_SUPPORTED



`ifdef DBG_CPU1_SUPPORTED
// Connecting cpu module
dbg_cpu i_dbg_cpu_8051 (
                  // JTAG signals
                  .tck_i            (tck_i),
                  .tdi_i            (cpu1_tdi),
                  .tdo_o            (cpu1_tdo),

                  // TAP states
                  .shift_dr_i       (shift_dr_i),
                  .pause_dr_i       (pause_dr_i),
                  .update_dr_i      (update_dr_i),

                  .cpu_ce_i         (cpu1_ce),
                  .crc_match_i      (crc_match),
                  .crc_en_o         (cpu1_crc_en),
                  .shift_crc_o      (cpu1_shift_crc),
                  .rst_i            (rst_i),

                  // CPU signals
                  .cpu_clk_i        (cpu1_clk_i), 
                  .cpu_addr_o       (cpu1_addr_o), 
                  .cpu_data_i       (cpu1_data_i), 
                  .cpu_data_o       (cpu1_data_o),
                  .cpu_bp_i         (cpu1_bp_i),
                  .cpu_stall_o      (cpu1_stall_o),
                  .cpu_stb_o        (cpu1_stb_o),
                  .cpu_we_o         (cpu1_we_o),
                  .cpu_ack_i        (cpu1_ack_i),
                  .cpu_rst_o        (cpu1_rst_o)
              );
`endif


endmodule
