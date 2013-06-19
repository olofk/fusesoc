module wb_arbiter
  #(
   // Bus parameters
   parameter dw = 32,
   parameter aw = 32)
  (
   // Clock, reset
   input 		wb_clk_i,
   input 		wb_rst_i,
   // Inputs
   input [aw-1:0]  wbm0_adr_i,
   input [1:0] 	   wbm0_bte_i,
   input [2:0] 	   wbm0_cti_i,
   input 	   wbm0_cyc_i,
   input [dw-1:0]  wbm0_dat_i,
   input [3:0] 	   wbm0_sel_i,
   input 	   wbm0_stb_i,
   input 	   wbm0_we_i,
   // Outputs
   output 	   wbm0_ack_o,
   output 	   wbm0_err_o,
   output 	   wbm0_rty_o,
   output [dw-1:0] wbm0_dat_o,
   // Inputs
   input [aw-1:0]  wbm1_adr_i,
   input [1:0] 	   wbm1_bte_i,
   input [2:0] 	   wbm1_cti_i,
   input 	   wbm1_cyc_i,
   input [dw-1:0]  wbm1_dat_i,
   input [3:0] 	   wbm1_sel_i,
   input 	   wbm1_stb_i,
   input 	   wbm1_we_i,
   // Outputs
   output 	   wbm1_ack_o,
   output 	   wbm1_err_o,
   output 	   wbm1_rty_o,
   output [dw-1:0] wbm1_dat_o,
    // Inputs
   input [aw-1:0]  wbm2_adr_i,
   input [1:0] 	   wbm2_bte_i,
   input [2:0] 	   wbm2_cti_i,
   input 	   wbm2_cyc_i,
   input [dw-1:0]  wbm2_dat_i,
   input [3:0] 	   wbm2_sel_i,
   input 	   wbm2_stb_i,
   input 	   wbm2_we_i,
   // Outputs
   output 	   wbm2_ack_o,
   output 	   wbm2_err_o,
   output 	   wbm2_rty_o,
   output [dw-1:0] wbm2_dat_o,
   //Slave interface
   output [aw-1:0] wbs_adr_o,
   output [dw-1:0] wbs_dat_o,
   output [3:0]    wbs_sel_o,
   output 	   wbs_we_o,
   output 	   wbs_cyc_o,
   output 	   wbs_stb_o,
   output [2:0]    wbs_cti_o,
   output [1:0]    wbs_bte_o,
   input [dw-1:0]  wbs_sdt_i,
   input 	   wbs_ack_i,
   input 	   wbs_err_i,
   input 	   wbs_rty_i);

   reg [2:0] 		input_select, last_selected;

   // Wires allowing selection of new input
   wire arb_for_wbm0 = (last_selected[1] | last_selected[2] | 
			  !wbm1_cyc_i | !wbm2_cyc_i) & !(|input_select);
   wire arb_for_wbm1 = (last_selected[0] | last_selected[2] | 
			  !wbm0_cyc_i | !wbm2_cyc_i) & !(|input_select);
   wire arb_for_wbm2 = (last_selected[0] | last_selected[1] | 
			  !wbm0_cyc_i | !wbm1_cyc_i) & !(|input_select);
   
   // Master select logic
   always @(posedge wb_clk_i)
     if (wb_rst_i)
       input_select <= 0;
     else if ((input_select[0] & !wbm0_cyc_i) | (input_select[1] & !wbm1_cyc_i)
	      | (input_select[2] & !wbm2_cyc_i))
       input_select <= 0;
     else if (!(&input_select) & wbm0_cyc_i & arb_for_wbm0)
       input_select <= 3'b001;
     else if (!(&input_select) & wbm1_cyc_i & arb_for_wbm1)
       input_select <= 3'b010;
     else if (!(&input_select) & wbm2_cyc_i & arb_for_wbm2)
       input_select <= 3'b100;
   
   always @(posedge wb_clk_i)
     if (wb_rst_i)
       last_selected <= 0;
     else if (!(&input_select) & wbm0_cyc_i & arb_for_wbm0)
       last_selected <= 3'b001;
     else if (!(&input_select) & wbm1_cyc_i & arb_for_wbm1)
       last_selected <= 3'b010;
     else if (!(&input_select) & wbm2_cyc_i & arb_for_wbm2)
       last_selected <= 3'b100;

   // Mux input signals to RAM (default to wbm0)
   assign wbs_adr_o = (input_select[2]) ? wbm2_adr_i : 
		 (input_select[1]) ? wbm1_adr_i : 
		 (input_select[0]) ? wbm0_adr_i : 0;
   assign wbs_bte_o = (input_select[2]) ? wbm2_bte_i : 
		 (input_select[1]) ? wbm1_bte_i : 
		 (input_select[0]) ? wbm0_bte_i : 0;
   assign wbs_cti_o = (input_select[2]) ? wbm2_cti_i : 
		 (input_select[1]) ? wbm1_cti_i : 
		 (input_select[0]) ? wbm0_cti_i : 0;
   assign wbs_cyc_o = (input_select[2]) ? wbm2_cyc_i : 
		 (input_select[1]) ? wbm1_cyc_i : 
		 (input_select[0]) ? wbm0_cyc_i : 0;
   assign wbs_dat_o = (input_select[2]) ? wbm2_dat_i : 
		 (input_select[1]) ? wbm1_dat_i : 
		 (input_select[0]) ? wbm0_dat_i : 0;
   assign wbs_sel_o = (input_select[2]) ? wbm2_sel_i : 
		 (input_select[1]) ? wbm1_sel_i : 
		 (input_select[0]) ? wbm0_sel_i : 0;
   assign wbs_stb_o = (input_select[2]) ? wbm2_stb_i : 
		 (input_select[1]) ? wbm1_stb_i : 
		 (input_select[0]) ? wbm0_stb_i : 0;
   assign wbs_we_o  = (input_select[2]) ? wbm2_we_i  :
		 (input_select[1]) ? wbm1_we_i  : 
		 (input_select[0]) ? wbm0_we_i : 0;

   // Output from RAM, gate the ACK, ERR, RTY signals appropriately
   assign wbm0_dat_o = wbs_sdt_i;
   assign wbm0_ack_o = wbs_ack_i & input_select[0];
   assign wbm0_err_o = wbs_err_i & input_select[0];   
   assign wbm0_rty_o = 0;

   assign wbm1_dat_o = wbs_sdt_i;
   assign wbm1_ack_o = wbs_ack_i & input_select[1];
   assign wbm1_err_o = wbs_err_i & input_select[1];
   assign wbm1_rty_o = 0;

   assign wbm2_dat_o = wbs_sdt_i;
   assign wbm2_ack_o = wbs_ack_i & input_select[2];
   assign wbm2_err_o = wbs_err_i & input_select[2];
   assign wbm2_rty_o = 0;
   
endmodule // wb_arbiter

