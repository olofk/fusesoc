module wb_data_resize
  #(parameter aw  = 32, //Address width
    parameter mdw = 32, //Master Data Width
    parameter sdw = 8) //Slave Data Width
   (//Wishbone Master interface
    input  [aw-1:0]  wbm_adr_i,
    input  [mdw-1:0] wbm_dat_i,
    input  [3:0]     wbm_sel_i,
    input 	     wbm_we_i,
    input 	     wbm_cyc_i,
    input 	     wbm_stb_i,
    input  [2:0]     wbm_cti_i,
    input  [1:0]     wbm_bte_i,
    output [mdw-1:0] wbm_sdt_o,
    output 	     wbm_ack_o,
    output 	     wbm_err_o,
    output 	     wbm_rty_o, 
    // Wishbone Slave interface
    output [aw-1:0]  wbs_adr_o,
    output [sdw-1:0] wbs_dat_o,
    output 	     wbs_we_o,
    output 	     wbs_cyc_o,
    output 	     wbs_stb_o,
    output [2:0]     wbs_cti_o,
    output [1:0]     wbs_bte_o,
    input  [sdw-1:0] wbs_sdt_i,
    input 	     wbs_ack_i,
    input 	     wbs_err_i,
    input 	     wbs_rty_i);

   assign wbs_adr_o = wbm_adr_i;
   assign wbs_dat_o = wbm_sel_i[3] ? wbm_dat_i[31:24] :
		      wbm_sel_i[2] ? wbm_dat_i[23:16] :
		      wbm_sel_i[1] ? wbm_dat_i[15:8]  :
		      wbm_sel_i[0] ? wbm_dat_i[7:0]   : 8'b0;
   
   assign wbs_we_o  = wbm_we_i;

   assign wbs_cyc_o = wbm_cyc_i;
   assign wbs_stb_o = wbm_stb_i;
   
   assign wbs_cti_o = wbm_cti_i;
   assign wbs_bte_o = wbm_bte_i;
   
   assign wbm_sdt_o = (wbm_sel_i[3]) ? {wbs_sdt_i, 24'd0} :
		      (wbm_sel_i[2]) ? {8'd0 , wbs_sdt_i, 16'd0} :
		      (wbm_sel_i[1]) ? {16'd0, wbs_sdt_i, 8'd0} :
	              {24'd0, wbs_sdt_i};
   assign wbm_ack_o = wbs_ack_i;
   assign wbm_err_o = wbs_err_i;
   assign wbm_rty_o = wbs_rty_i;
   
endmodule
