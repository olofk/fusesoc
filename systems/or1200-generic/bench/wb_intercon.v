module wb_intercon
  #(parameter aw = 32,
    parameter dw = 32)
  (input 	   wb_clk_i,
   input 	   wb_rst_i,
   // OR1200 Instruction bus (To Master)
   input [aw-1:0]  wb_or1200_i_adr_i,
   input [dw-1:0]  wb_or1200_i_dat_i,
   input [3:0] 	   wb_or1200_i_sel_i,
   input 	   wb_or1200_i_we_i,
   input 	   wb_or1200_i_cyc_i,
   input 	   wb_or1200_i_stb_i,
   input [2:0] 	   wb_or1200_i_cti_i,
   input [1:0] 	   wb_or1200_i_bte_i,
   output [dw-1:0] wb_or1200_i_dat_o,
   output 	   wb_or1200_i_ack_o,
   output 	   wb_or1200_i_err_o,
   output 	   wb_or1200_i_rty_o,
   // OR1200 Data bus (To Master)
   input [aw-1:0]  wb_or1200_d_adr_i,
   input [dw-1:0]  wb_or1200_d_dat_i,
   input [3:0] 	   wb_or1200_d_sel_i,
   input 	   wb_or1200_d_we_i,
   input 	   wb_or1200_d_cyc_i,
   input 	   wb_or1200_d_stb_i,
   input [2:0] 	   wb_or1200_d_cti_i,
   input [1:0] 	   wb_or1200_d_bte_i,
   output [dw-1:0] wb_or1200_d_dat_o,
   output 	   wb_or1200_d_ack_o,
   output 	   wb_or1200_d_err_o,
   output 	   wb_or1200_d_rty_o,
   // Memory Interface (To Slave)
   output [aw-1:0] wb_mem_adr_o,
   output [dw-1:0] wb_mem_dat_o,
   output [3:0]    wb_mem_sel_o,
   output 	   wb_mem_we_o,
   output 	   wb_mem_cyc_o,
   output 	   wb_mem_stb_o,
   output [2:0]    wb_mem_cti_o,
   output [1:0]    wb_mem_bte_o,
   input [dw-1:0]  wb_mem_dat_i,
   input 	   wb_mem_ack_i,
   input 	   wb_mem_err_i,
   input 	   wb_mem_rty_i);

   localparam MASTERS = 2;
   
   wire [MASTERS*aw-1:0] wbm_adr;
   wire [MASTERS*dw-1:0] wbm_dat;
   wire [MASTERS*4-1:0]  wbm_sel;
   wire [MASTERS-1:0] 	 wbm_we ;
   wire [MASTERS-1:0] 	 wbm_cyc;
   wire [MASTERS-1:0] 	 wbm_stb;
   wire [MASTERS*3-1:0]  wbm_cti;
   wire [MASTERS*2-1:0]  wbm_bte;
   wire [MASTERS*dw-1:0] wbm_sdt;
   wire [MASTERS-1:0] 	 wbm_ack;
   wire [MASTERS-1:0] 	 wbm_err;
   wire [MASTERS-1:0] 	 wbm_rty;

   assign wbm_adr[0*dw+:dw] = wb_or1200_i_adr_i;
   assign wbm_dat[0*aw+:aw] = wb_or1200_i_dat_i;
   assign wbm_sel[0*4+:4]   = wb_or1200_i_sel_i;
   assign wbm_we[0]	    = wb_or1200_i_we_i;
   assign wbm_cyc[0] 	    = wb_or1200_i_cyc_i;
   assign wbm_stb[0]	    = wb_or1200_i_stb_i;
   assign wbm_cti[0*3+:3]   = wb_or1200_i_cti_i;
   assign wbm_bte[0*2+:2]   = wb_or1200_i_bte_i;
   assign wb_or1200_i_dat_o = wbm_sdt[0*dw+:dw];
   assign wb_or1200_i_ack_o = wbm_ack[0];
   assign wb_or1200_i_err_o = wbm_err[0];
   assign wb_or1200_i_rty_o = wbm_rty[0]; 

   assign wbm_adr[1*dw+:dw] = wb_or1200_d_adr_i;
   assign wbm_dat[1*aw+:aw] = wb_or1200_d_dat_i;
   assign wbm_sel[1*4+:4]   = wb_or1200_d_sel_i;
   assign wbm_we[1]	    = wb_or1200_d_we_i;
   assign wbm_cyc[1] 	    = wb_or1200_d_cyc_i;
   assign wbm_stb[1]	    = wb_or1200_d_stb_i;
   assign wbm_cti[1*3+:3]   = wb_or1200_d_cti_i;
   assign wbm_bte[1*2+:2]   = wb_or1200_d_bte_i;
   assign wb_or1200_d_dat_o = wbm_sdt[1*dw+:dw];
   assign wb_or1200_d_ack_o = wbm_ack[1];
   assign wb_or1200_d_err_o = wbm_err[1];
   assign wb_or1200_d_rty_o = wbm_rty[1]; 
   
   //Memory Arbiter
   wb_arbiter wb_arbiter0
     (
      // Clock, reset
      .wb_clk_i				(wb_clk_i),
      .wb_rst_i				(wb_rst_i),
      // Wishbone master connections
      .wbm_adr_i			(wbm_adr),
      .wbm_dat_i			(wbm_dat),
      .wbm_sel_i			(wbm_sel),
      .wbm_we_i			        (wbm_we ),
      .wbm_cyc_i			(wbm_cyc),
      .wbm_stb_i			(wbm_stb),
      .wbm_cti_i			(wbm_cti),
      .wbm_bte_i			(wbm_bte),
      .wbm_dat_o			(wbm_sdt),
      .wbm_ack_o			(wbm_ack),
      .wbm_err_o                        (wbm_err),
      .wbm_rty_o                        (wbm_rty),
      //Wishbone Master interface
      .wbs_adr_o			(wb_mem_adr_o),
      .wbs_dat_o			(wb_mem_dat_o),
      .wbs_sel_o			(wb_mem_sel_o),
      .wbs_we_o			        (wb_mem_we_o ),
      .wbs_cyc_o			(wb_mem_cyc_o),
      .wbs_stb_o			(wb_mem_stb_o),
      .wbs_cti_o			(wb_mem_cti_o),
      .wbs_bte_o			(wb_mem_bte_o),
      .wbs_dat_i			(wb_mem_dat_i),
      .wbs_ack_i			(wb_mem_ack_i),
      .wbs_err_i                        (wb_mem_err_i),
      .wbs_rty_i                        (wb_mem_rty_i));
         
endmodule // wb_intercon
