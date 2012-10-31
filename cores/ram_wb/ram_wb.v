module ram_wb
  #(
   // Bus parameters
   parameter dw = 32,
   parameter aw = 32,
   // Memory parameters
   parameter mem_size_bytes = 32'h0000_0400, // 1KBytes
   parameter mem_adr_width = 10, //(log2(mem_span));
   parameter memory_file = "")
  (
   // Clock, reset
   input 		wb_clk_i,
   input 		wb_rst_i,
   // Inputs
   input [aw-1:0]	wbm0_adr_i,
   input [1:0] 		wbm0_bte_i,
   input [2:0] 		wbm0_cti_i,
   input 		wbm0_cyc_i,
   input [dw-1:0] 	wbm0_dat_i,
   input [3:0] 		wbm0_sel_i,
   input 		wbm0_stb_i,
   input 		wbm0_we_i,
   // Outputs
   output 		wbm0_ack_o,
   output 		wbm0_err_o,
   output 		wbm0_rty_o,
   output [dw-1:0] 	wbm0_dat_o,
   // Inputs
   input [aw-1:0]	wbm1_adr_i,
   input [1:0] 		wbm1_bte_i,
   input [2:0] 		wbm1_cti_i,
   input 		wbm1_cyc_i,
   input [dw-1:0] 	wbm1_dat_i,
   input [3:0] 		wbm1_sel_i,
   input 		wbm1_stb_i,
   input 		wbm1_we_i,
   // Outputs
   output 		wbm1_ack_o,
   output 		wbm1_err_o,
   output 		wbm1_rty_o,
   output [dw-1:0] 	wbm1_dat_o,
    // Inputs
   input [aw-1:0]	wbm2_adr_i,
   input [1:0] 		wbm2_bte_i,
   input [2:0] 		wbm2_cti_i,
   input 		wbm2_cyc_i,
   input [dw-1:0] 	wbm2_dat_i,
   input [3:0] 		wbm2_sel_i,
   input 		wbm2_stb_i,
   input 		wbm2_we_i,
   // Outputs
   output 		wbm2_ack_o,
   output 		wbm2_err_o,
   output 		wbm2_rty_o,
   output [dw-1:0] 	wbm2_dat_o
   );

   // Internal wires to actual RAM

   wire 		wbs_ram_ack_o;
   wire 		wbs_ram_err_o;
   wire 		wbs_ram_rty_o;
   wire [dw-1:0] 	wbs_ram_dat_o;

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
   wire [aw-1:0] wbs_ram_adr_i = (input_select[2]) ? wbm2_adr_i : 
		 (input_select[1]) ? wbm1_adr_i : 
		 (input_select[0]) ? wbm0_adr_i : 0;
   wire [1:0] 	 wbs_ram_bte_i = (input_select[2]) ? wbm2_bte_i : 
		 (input_select[1]) ? wbm1_bte_i : 
		 (input_select[0]) ? wbm0_bte_i : 0;
   wire [2:0] 	 wbs_ram_cti_i = (input_select[2]) ? wbm2_cti_i : 
		 (input_select[1]) ? wbm1_cti_i : 
		 (input_select[0]) ? wbm0_cti_i : 0;
   wire 	 wbs_ram_cyc_i = (input_select[2]) ? wbm2_cyc_i : 
		 (input_select[1]) ? wbm1_cyc_i : 
		 (input_select[0]) ? wbm0_cyc_i : 0;
   wire [dw-1:0] wbs_ram_dat_i = (input_select[2]) ? wbm2_dat_i : 
		 (input_select[1]) ? wbm1_dat_i : 
		 (input_select[0]) ? wbm0_dat_i : 0;
   wire [3:0] 	 wbs_ram_sel_i = (input_select[2]) ? wbm2_sel_i : 
		 (input_select[1]) ? wbm1_sel_i : 
		 (input_select[0]) ? wbm0_sel_i : 0;
   wire 	 wbs_ram_stb_i = (input_select[2]) ? wbm2_stb_i : 
		 (input_select[1]) ? wbm1_stb_i : 
		 (input_select[0]) ? wbm0_stb_i : 0;
   wire 	 wbs_ram_we_i  = (input_select[2]) ? wbm2_we_i  :
		 (input_select[1]) ? wbm1_we_i  : 
		 (input_select[0]) ? wbm0_we_i : 0;

   // Output from RAM, gate the ACK, ERR, RTY signals appropriately
   assign wbm0_dat_o = wbs_ram_dat_o;
   assign wbm0_ack_o = wbs_ram_ack_o & input_select[0];
   assign wbm0_err_o = wbs_ram_err_o & input_select[0];   
   assign wbm0_rty_o = 0;

   assign wbm1_dat_o = wbs_ram_dat_o;
   assign wbm1_ack_o = wbs_ram_ack_o & input_select[1];
   assign wbm1_err_o = wbs_ram_err_o & input_select[1];
   assign wbm1_rty_o = 0;

   assign wbm2_dat_o = wbs_ram_dat_o;
   assign wbm2_ack_o = wbs_ram_ack_o & input_select[2];
   assign wbm2_err_o = wbs_ram_err_o & input_select[2];
   assign wbm2_rty_o = 0;
   
   ram_wb_b3
     #(.memory_file(memory_file),
       .aw(aw),
       .dw(dw),
       .mem_size_bytes(mem_size_bytes),
       .mem_adr_width(mem_adr_width))
   ram_wb_b3_0
     (
      // Outputs
      .wb_ack_o				(wbs_ram_ack_o),
      .wb_err_o				(wbs_ram_err_o),
      .wb_rty_o				(wbs_ram_rty_o),
      .wb_dat_o				(wbs_ram_dat_o),
      // Inputs
      .wb_adr_i				(wbs_ram_adr_i),
      .wb_bte_i				(wbs_ram_bte_i),
      .wb_cti_i				(wbs_ram_cti_i),
      .wb_cyc_i				(wbs_ram_cyc_i),
      .wb_dat_i				(wbs_ram_dat_i),
      .wb_sel_i				(wbs_ram_sel_i),
      .wb_stb_i				(wbs_ram_stb_i),
      .wb_we_i				(wbs_ram_we_i),
      .wb_clk_i				(wb_clk_i),
      .wb_rst_i				(wb_rst_i));

endmodule // ram_wb


