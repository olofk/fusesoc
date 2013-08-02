module wb_arbiter_tb
  #(parameter NUM_MASTERS = 5)
  (input wb_clk_i,
   input wb_rst_i,
   output done);

   localparam aw = 32;
   localparam dw = 32;

   localparam MEMORY_SIZE_BITS  = 8;
   localparam MEMORY_SIZE_WORDS = 2**MEMORY_SIZE_BITS;
   
   wire [aw-1:0] wbs_adr;
   wire [dw-1:0] wbs_dat;
   wire [3:0] 	 wbs_sel;
   wire 	 wbs_we ;
   wire 	 wbs_cyc;
   wire 	 wbs_stb;
   wire [2:0] 	 wbs_cti;
   wire [1:0] 	 wbs_bte;
   wire [dw-1:0] wbs_sdt;
   wire 	 wbs_ack;
   wire 	 wbs_err;
   wire 	 wbs_rty;

   wire [NUM_MASTERS*aw-1:0] 	 wbm_adr;
   wire [NUM_MASTERS*dw-1:0] 	 wbm_dat;
   wire [NUM_MASTERS*4-1:0] 	 wbm_sel;
   wire [NUM_MASTERS-1:0] 	 wbm_we ;
   wire [NUM_MASTERS-1:0]	 wbm_cyc;
   wire [NUM_MASTERS-1:0]	 wbm_stb;
   wire [NUM_MASTERS*3-1:0] 	 wbm_cti;
   wire [NUM_MASTERS*2-1:0] 	 wbm_bte;
   wire [NUM_MASTERS*dw-1:0] 	 wbm_sdt;
   wire [NUM_MASTERS-1:0]	 wbm_ack;
   wire [NUM_MASTERS-1:0] 	 wbm_err;
   wire [NUM_MASTERS-1:0] 	 wbm_rty;

   wire [31:0] 	 slave_writes;
   wire [31:0] 	 slave_reads;
   wire [NUM_MASTERS-1:0] done_int;

   genvar 	 i;
   
   generate
      for(i=0;i<NUM_MASTERS;i=i+1) begin : masters
	 wb_master
	    #(.MEMORY_SIZE_BITS(MEMORY_SIZE_BITS),
	      .MEM_RANGE_START (i*MEMORY_SIZE_WORDS))
	 wb_master0
	    (.wb_clk_i (wb_clk_i),
	     .wb_rst_i (wb_rst_i),
	     .wb_adr_o (wbm_adr[i*aw+:aw]),
	     .wb_dat_o (wbm_dat[i*dw+:dw]),
	     .wb_sel_o (wbm_sel[i*4+:4]),
	     .wb_we_o  (wbm_we[i] ), 
	     .wb_cyc_o (wbm_cyc[i]),
	     .wb_stb_o (wbm_stb[i]),
	     .wb_cti_o (wbm_cti[i*3+:3]),
	     .wb_bte_o (wbm_bte[i*2+:2]),
	     .wb_sdt_i (wbm_sdt[i*dw+:dw]),
	     .wb_ack_i (wbm_ack[i]),
	     .wb_err_i (wbm_err[i]),
	     .wb_rty_i (wbm_rty[i]),
	     //Test Control
	     .done(done_int[i]));
      end // block: slaves
   endgenerate
   
   integer 	 idx;

   assign done = &done_int;
   
   always @(done) begin
      if(done === 1) begin
	 $display("Average wait times");
	 for(idx=0;idx<NUM_MASTERS;idx=idx+1)
	   $display("Master %0d : %f",idx, ack_delay[idx]/num_transactions[idx]);
	 $display("All tests passed!");
      end
   end

   wb_arbiter
     #(.num_masters(NUM_MASTERS))
   wb_arbiter0
     (.wb_clk_i    (wb_clk_i),
      .wb_rst_i     (wb_rst_i),
      
      // Master Interface
      .wbm_adr_i (wbm_adr),
      .wbm_dat_i (wbm_dat),
      .wbm_sel_i (wbm_sel),
      .wbm_we_i  (wbm_we ),
      .wbm_cyc_i (wbm_cyc),
      .wbm_stb_i (wbm_stb),
      .wbm_cti_i (wbm_cti),
      .wbm_bte_i (wbm_bte),
      .wbm_dat_o (wbm_sdt),
      .wbm_ack_o (wbm_ack),
      .wbm_err_o (wbm_err),
      .wbm_rty_o (wbm_rty), 
      // Wishbone Slave interface
      .wbs_adr_o (wbs_adr),
      .wbs_dat_o (wbs_dat),
      .wbs_sel_o (wbs_sel), 
      .wbs_we_o  (wbs_we),
      .wbs_cyc_o (wbs_cyc),
      .wbs_stb_o (wbs_stb),
      .wbs_cti_o (wbs_cti),
      .wbs_bte_o (wbs_bte),
      .wbs_dat_i (wbs_sdt),
      .wbs_ack_i (wbs_ack),
      .wbs_err_i (wbs_err),
      .wbs_rty_i (wbs_rty));
   
   assign slave_writes = wb_mem_model0.writes;
   assign slave_reads  = wb_mem_model0.reads;

   time start_time[NUM_MASTERS-1:0];
   time ack_delay[NUM_MASTERS-1:0];
   integer num_transactions[NUM_MASTERS-1:0];

   generate
      for(i=0;i<NUM_MASTERS;i=i+1) begin : wait_time
	 initial begin
	    ack_delay[i] = 0;
	    num_transactions[i] = 0;
	    while(1) begin
	       @(posedge wbm_cyc[i]);
	       start_time[i] = $time;
	       @(posedge wbm_ack[i]);
	       ack_delay[i] = ack_delay[i] + $time-start_time[i];
	       num_transactions[i] = num_transactions[i]+1;
	    end
	 end
      end
   endgenerate
      
   wb_bfm_memory #(.DEBUG (0),
		   .mem_size_bytes(MEMORY_SIZE_WORDS*(dw/8)*NUM_MASTERS))
   wb_mem_model0
     (.wb_clk_i (wb_clk_i),
      .wb_rst_i (wb_rst_i),
      .wb_adr_i (wbs_adr),
      .wb_dat_i (wbs_dat),
      .wb_sel_i (wbs_sel),
      .wb_we_i  (wbs_we),
      .wb_cyc_i (wbs_cyc),
      .wb_stb_i (wbs_stb),
      .wb_cti_i (wbs_cti),
      .wb_bte_i (wbs_bte),
      .wb_sdt_o (wbs_sdt),
      .wb_ack_o (wbs_ack),
      .wb_err_o (wbs_err),
      .wb_rty_o (wbs_rty));
endmodule
