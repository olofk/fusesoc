module orpsoc_tb;

   vlog_tb_utils vlog_tb_utils0();
   
   localparam aw = 32;
   localparam dw = 32;
   
   reg	   wb_clk = 1'b1;
   reg	   wb_rst = 1'b1;
   
   always #5 wb_clk <= ~wb_clk;
   initial  #100 wb_rst <= 0;
   
   wire [aw-1:0] wb_adr;
   wire [dw-1:0] wb_dat;
   wire [3:0] 	 wb_sel;
   wire 	 wb_we ;
   wire 	 wb_cyc;
   wire 	 wb_stb;
   wire [2:0] 	 wb_cti;
   wire [1:0] 	 wb_bte;
   wire [dw-1:0] wb_sdt;
   wire 	 wb_ack;
   wire 	 wb_err;
   wire 	 wb_rty;

   wb_master wb_master0
     (.wb_clk_i (wb_clk),
      .wb_rst_i (wb_rst),
      .wb_adr_o (wb_adr),
      .wb_dat_o (wb_dat),
      .wb_sel_o (wb_sel),
      .wb_we_o  (wb_we ), 
      .wb_cyc_o (wb_cyc),
      .wb_stb_o (wb_stb),
      .wb_cti_o (wb_cti),
      .wb_bte_o (wb_bte),
      .wb_sdt_i (wb_sdt),
      .wb_ack_i (wb_ack),
      .wb_err_i (wb_err),
      .wb_rty_i (wb_rty));
   
   wb_bfm_memory #(.DEBUG (0))
   wb_mem_model0
     (.wb_clk_i (wb_clk),
      .wb_rst_i (wb_rst),
      .wb_adr_i (wb_adr),
      .wb_dat_i (wb_dat),
      .wb_sel_i (wb_sel),
      .wb_we_i  (wb_we ), 
      .wb_cyc_i (wb_cyc),
      .wb_stb_i (wb_stb),
      .wb_cti_i (wb_cti),
      .wb_bte_i (wb_bte),
      .wb_sdt_o (wb_sdt),
      .wb_ack_o (wb_ack),
      .wb_err_o (wb_err),
      .wb_rty_o (wb_rty));
endmodule // orpsoc_tb
