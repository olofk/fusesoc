module wb_mux_tb
  #(parameter NUM_SLAVES = 2)
  (input wb_clk_i,
   input wb_rst_i,
   output done);

   localparam aw = 32;
   localparam dw = 32;

   localparam MEMORY_SIZE_WORDS = 32'h100;
   localparam MEMORY_SIZE_BITS  = 8;
   
   wire [aw-1:0] wbs_adr;
   wire [dw-1:0] wbs_dat;
   wire [3:0] 	 wbs_sel;
   wire 	 wbs_we ;
   wire [NUM_SLAVES-1:0] wbs_cyc;
   wire 		 wbs_stb;
   wire [2:0] 	 wbs_cti;
   wire [1:0] 	 wbs_bte;
   wire [NUM_SLAVES*dw-1:0] wbs_sdt;
   wire [NUM_SLAVES-1:0]	 wbs_ack;
   wire [NUM_SLAVES-1:0]	 wbs_err;
   wire [NUM_SLAVES-1:0]	 wbs_rty;

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

   wire [31:0] 	 slave_writes [0:NUM_SLAVES-1];
   wire [31:0] 	 slave_reads  [0:NUM_SLAVES-1];
   
   genvar 	 i;
   
   wb_master
     #(.MEMORY_SIZE_BITS(MEMORY_SIZE_BITS+$clog2(NUM_SLAVES)))
   wb_master0
     (.wb_clk_i (wb_clk_i),
      .wb_rst_i (wb_rst_i),
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
      .wb_rty_i (wb_rty),
      //Test Control
      .done(done));
   
   integer 	 idx;
   
   always @(done) begin
      if(done === 1'b1) begin
	 for(idx=0;idx<NUM_SLAVES;idx=idx+1) begin
	    $display("%0d writes to slave %0d", slave_writes[idx], idx);
	 end
	 $display("All tests passed!");
      end
   end

   wire [NUM_SLAVES-1:0] slave_sel;

   generate
      for(i=0;i<NUM_SLAVES;i=i+1) begin : gen_slave_sel
	assign slave_sel[i] = (wb_adr[31:MEMORY_SIZE_BITS] == i);
      end
   endgenerate
   
   wb_mux
     #(.num_slaves(NUM_SLAVES))
   wb_mux0
   (.wb_clk    (wb_clk_i),
    .wb_rst     (wb_rst_i),

    .slave_sel_i (slave_sel),
    // Master Interface
    .wbm_adr_i (wb_adr),
    .wbm_dat_i (wb_dat),
    .wbm_sel_i (wb_sel),
    .wbm_we_i  (wb_we ),
    .wbm_cyc_i (wb_cyc),
    .wbm_stb_i (wb_stb),
    .wbm_cti_i (wb_cti),
    .wbm_bte_i (wb_bte),
    .wbm_sdt_o (wb_sdt),
    .wbm_ack_o (wb_ack),
    .wbm_err_o (wb_err),
    .wbm_rty_o (wb_rty), 
    // Wishbone Slave interface
    .wbs_adr_o (wbs_adr),
    .wbs_dat_o (wbs_dat),
    .wbs_sel_o (wbs_sel), 
    .wbs_we_o  (wbs_we),
    .wbs_cyc_o (wbs_cyc),
    .wbs_stb_o (wbs_stb),
    .wbs_cti_o (wbs_cti),
    .wbs_bte_o (wbs_bte),
    .wbs_sdt_i (wbs_sdt),
    .wbs_ack_i (wbs_ack),
    .wbs_err_i (wbs_err),
    .wbs_rty_i (wbs_rty));
   
   generate
      for(i=0;i<NUM_SLAVES;i=i+1) begin : slaves
	 assign slave_writes[i] = wb_mem_model0.writes;
	 assign slave_reads[i]  = wb_mem_model0.reads;
	 
	 wb_bfm_memory #(.DEBUG (0),
			 .mem_size_bytes(MEMORY_SIZE_WORDS*(dw/8)))
	 wb_mem_model0
	    (.wb_clk_i (wb_clk_i),
	     .wb_rst_i (wb_rst_i),
	     .wb_adr_i (wbs_adr & (2**MEMORY_SIZE_BITS-1)),
	     .wb_dat_i (wbs_dat),
	     .wb_sel_i (wbs_sel),
	     .wb_we_i  (wbs_we),
	     .wb_cyc_i (wbs_cyc[i]),
	     .wb_stb_i (wbs_stb),
	     .wb_cti_i (wbs_cti),
	     .wb_bte_i (wbs_bte),
	     .wb_sdt_o (wbs_sdt[i*dw+:dw]),
	     .wb_ack_o (wbs_ack[i]),
	     .wb_err_o (wbs_err[i]),
	     .wb_rty_o (wbs_rty[i]));
      end // block: slaves
   endgenerate
   
endmodule // orpsoc_tb
