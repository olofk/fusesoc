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

module arbiter
  (
   input wb_clk,
   input wb_rst,

   // Wishbone Master Interface
   input  [num_masters*wb_adr_width-1:0] wbm_adr_o,
   input  [num_masters*wb_dat_width-1:0] wbm_dat_o,
   input  [num_masters*4-1:0]            wbm_sel_o,
   input  [num_masters-1:0]              wbm_we_o,
   input  [num_masters-1:0]              wbm_cyc_o,
   input  [num_masters-1:0]              wbm_stb_o,
   input  [num_masters*3-1:0]            wbm_cti_o,
   input  [num_masters*2-1:0]            wbm_bte_o,
   output [num_masters*wb_dat_width-1:0] wbm_dat_i,
   output [num_masters-1:0]              wbm_ack_i,
   output [num_masters-1:0]              wbm_err_i,
   output [num_masters-1:0]              wbm_rty_i,   

   // Wishbone Slave interface
   output [num_slaves*wb_adr_width-1:0]  wbs_adr_i,
   output [num_slaves*wb_dat_width-1:0]  wbs_dat_i,
   output [num_slaves*4-1:0]             wbs_sel_i,  
   output [num_slaves-1:0]               wbs_we_i,
   output [num_slaves-1:0]               wbs_cyc_i,
   output [num_slaves-1:0]               wbs_stb_i,
   output [num_slaves*3-1:0]             wbs_cti_i,
   output [num_slaves*2-1:0]             wbs_bte_i,
   input  [num_slaves*wb_dat_width-1:0]  wbs_dat_o,
   input  [num_slaves-1:0]               wbs_ack_o,
   input  [num_slaves-1:0]               wbs_err_o,
   input  [num_slaves-1:0]               wbs_rty_o
   );


///////////////////////////////////////////////////////////////////////////////
// Parameters
///////////////////////////////////////////////////////////////////////////////

   //Set to non-zero to enable watchdog
   parameter watchdog = 0;
   parameter watchdog_timer_width = 9;

   parameter wb_dat_width = 32;
   parameter wb_adr_width = 32;

   parameter wb_adr_match_width = 8;

   parameter num_slaves  = 2;
   parameter num_masters = 1;
   parameter registered = 1;

   genvar i;
   // Slave addresses. Each slave has an 8-bit address fieldFIXME
   parameter slave_adr = {num_slaves*wb_adr_match_width{1'b0}};
      
`define WB_ARB_ADDR_MATCH_SEL wb_adr_width-1:wb_adr_width-wb_adr_match_width//FIXME
   
   
///////////////////////////////////////////////////////////////////////////////
// Watchdog timer
///////////////////////////////////////////////////////////////////////////////
generate
if (watchdog == 1)
begin : gen_watchdog_timer
     
   reg [watchdog_timer_width:0] watchdog_timer;
   reg                       wbm_stb_r; // Register strobe
   wire                      wbm_stb_edge; // Detect its edge

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
end
else
begin : no_watchdog_timer
   assign watchdog_err = 0;
end
endgenerate

///////////////////////////////////////////////////////////////////////////////
// Master Side
///////////////////////////////////////////////////////////////////////////////
   
   // Master select (MUX controls)
   reg [1:0]                master_sel;

generate
   for(i=0;i<num_masters;i=i+1)
   begin : gen_master_sel
      always @(wbm_cyc)
	if(wbm_cyc_o[i] == 1)
	  master_sel <= i;
   end
endgenerate
   
		       

   // Register muxed master signals
/*   always @(posedge wb_clk)
     begin
        wbm_stb_o_r <= wbm_stb_o_w & !wbm_ack_i & !wbm_ack_i_r;//FIXME
     end // always @ (posedge wb_clk)
*/
   wire [0:num_masters-1] master_mask;
   
   assign wbm_dat_i = {num_masters{wbm_sdt}};
   assign wbm_ack_i = {num_masters{wbm_ack}} & master_mask;
   assign wbm_err_i = {num_masters{wbm_err}} & master_mask;
   assign wbm_err_i = {num_masters{wbm_err}} & master_mask;
   
   //Mux active master
   wire [wb_adr_width-1:0] wbm_adr = wbm_adr_arr[master_sel*wb_adr_width+:wb_adr_width];
   wire [wb_dat_width-1:0] wbm_dat = wbm_dat_arr[master_sel*wb_dat_width+:wb_dat_width];
   wire              [3:0] wbm_sel = wbm_sel_arr[master_sel*4+:4];
   wire                    wbm_we  = wbm_we_o   [master_sel];
   wire                    wbm_cyc = wbm_cyc_o  [master_sel];
   wire                    wbm_stb = wbm_stb_o  [master_sel];
   wire              [2:0] wbm_cti = wbm_cti_arr[master_sel*3+:3];
   wire              [1:0] wbm_bte = wbm_bte_arr[master_sel*2+:2];


///////////////////////////////////////////////////////////////////////////////
// Master/slave connection
///////////////////////////////////////////////////////////////////////////////

//Create combinatorial or registered connection between active master and slave
generate
   if(registered == 0)
   begin : gen_combinatorial
      wire wbs_adr = wbm_adr;
      wire wbs_dat = wbm_dat;
      wire wbs_sel = wbm_sel;
      wire wbs_we  = wbm_we;
      wire wbs_cyc = wbm_cyc;
      wire wbs_stb = wbm_stb;
      wire wbs_cti = wbm_cti;
      wire wbs_bte = wbm_bte;
      
      wire wbm_sdt = wbs_sdt;
      wire wbm_ack = wbs_ack;
      wire wbm_err = wbs_err;
      wire wbm_rty = wbs_rty;
   end
   else
   begin : gen_registered
      reg [wb_adr_width-1:0] wbs_adr;
      reg wbs_dat;
      reg wbs_sel;
      reg wbs_we;
      reg wbs_cyc;
      reg wbs_stb;
      reg wbs_cti;
      reg wbs_bte;
      
      reg wbm_sdt;
      reg wbm_ack;
      reg wbm_err;
      reg wbm_rty;
      
      always @(posedge wb_clk)
      begin
         wbs_adr <= wbm_adr;
         wbs_dat <= wbm_dat;
         wbs_sel <= wbm_sel;
         wbs_we  <= wbm_we;
         wbs_cyc <= wbm_cyc;
         wbs_stb <= wbm_stb;
         wbs_cti <= wbm_cti;
         wbs_bte <= wbm_bte;
      
         wbm_sdt <= wbs_sdt;
         wbm_ack <= wbs_ack;//FIXME
         wbm_err <= wbs_err;
         wbm_rty <= wbs_rty;
      end
   end
endgenerate
   
///////////////////////////////////////////////////////////////////////////////
// Slave Side
///////////////////////////////////////////////////////////////////////////////
  
   // Slave select wire
   wire [num_slaves-1:0]  slave_sel;
   reg [num_slaves-1:0]   slave_sel_r;

   // Register wb_slave_sel_r to break combinatorial loop when selecting default
   // slave
   always @(posedge wb_clk)
     slave_sel_r <= slave_sel;

generate
for(i=num_slaves-1;i==0;i=i-1)
begin : gen_slave
   if (wbm_adr_o[`WB_ARB_ADDR_MATCH_SEL] == (slave_adr>>(i*wb_adr_match_width) & {wb_adr_match_width{1}}))
     assign slave_sel = i;
end
endgenerate
   assign wbs_adr_i = {num_slaves{wbs_adr}};
   assign wbs_dat_i = {num_slaves{wbs_dat}};
   //FIXME wbs_sel_i
   assign wbs_we_i  = {num_slaves{wbs_we }};
   assign wbs_cyc_i = {num_slaves{wbs_cyc}} & wb_slave_sel_r;
   assign wbs_stb_i = {num_slaves{wbs_stb}} & wb_slave_sel_r;
   assign wbs_cti_i = {num_slaves{wbs_cti}};
   assign wbs_bte_i = {num_slaves{wbs_bte}};

   wire [wb_dat_width-1:0] wbs_sdt = wbs_dat_o[slave_sel*wb_dat_width+:wb_dat_width];
   wire                    wbs_ack = wbs_ack_o[slave_sel];
   wire                    wbs_err = wbs_err_o[slave_sel] | watchdog_err;
   wire                    wbs_rty = wbs_rty_o[slave_sel];

endmodule // arbiter
