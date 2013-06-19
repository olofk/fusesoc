module orpsoc_top;

   localparam wb_aw = 32;
   localparam wb_dw = 32;
   
   ////////////////////////////////////////////////////////////////////////
   //
   // Clock and reset generation
   // 
   ////////////////////////////////////////////////////////////////////////
   reg wb_clk = 1;
   reg wb_rst = 1;

   always #5 wb_clk <= ~wb_clk;
   initial #100 wb_rst <= 0;
   
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

   // memory wires
   wire [31:0]                wb_mem_adr;
   wire [31:0] 		      wb_mem_dat;
   wire [3:0] 		      wb_mem_sel;
   wire 		      wb_mem_we;
   wire 		      wb_mem_cyc;
   wire 		      wb_mem_stb;
   wire [2:0] 		      wb_mem_cti;
   wire [1:0] 		      wb_mem_bte;
   wire [31:0] 		      wb_mem_sdt;   
   wire 		      wb_mem_ack;
   wire 		      wb_mem_err;
   wire 		      wb_mem_rty;   
   

   ////////////////////////////////////////////////////////////////////////
   //
   // or1200
   // 
   ////////////////////////////////////////////////////////////////////////

   wire [19:0] 				  or1200_pic_ints;

   or1200_top #(.boot_adr(32'h00000100)) or1200_top0
       (
	// Instruction bus, clocks, reset
	.iwb_clk_i			(wb_clk),
	.iwb_rst_i			(wb_rst),
	.iwb_adr_o			(wb_or1200_i_adr),
	.iwb_dat_o			(wb_or1200_i_dat),
	.iwb_sel_o			(wb_or1200_i_sel),
	.iwb_we_o			(wb_or1200_i_we ),
	.iwb_cyc_o			(wb_or1200_i_cyc),
	.iwb_stb_o			(wb_or1200_i_stb),
	.iwb_cti_o			(wb_or1200_i_cti),
	.iwb_bte_o			(wb_or1200_i_bte),
	.iwb_dat_i			(wb_or1200_i_sdt),
	.iwb_ack_i			(wb_or1200_i_ack),
	.iwb_err_i			(wb_or1200_i_err),
	.iwb_rty_i			(wb_or1200_i_rty),
	// Data bus, clocks, reset            
	.dwb_clk_i			(wb_clk),
	.dwb_rst_i			(wb_rst),
	.dwb_adr_o			(wb_or1200_d_adr),
	.dwb_dat_o			(wb_or1200_d_dat),
	.dwb_sel_o			(wb_or1200_d_sel),
	.dwb_we_o			(wb_or1200_d_we),
	.dwb_cyc_o			(wb_or1200_d_cyc),
	.dwb_stb_o			(wb_or1200_d_stb),
	.dwb_cti_o			(wb_or1200_d_cti),
	.dwb_bte_o			(wb_or1200_d_bte),
	.dwb_dat_i			(wb_or1200_d_sdt),
	.dwb_ack_i			(wb_or1200_d_ack),
	.dwb_err_i			(wb_or1200_d_err),
	.dwb_rty_i			(wb_or1200_d_rty),

	// Debug interface ports
	.dbg_stall_i			(1'b0),
	.dbg_ewt_i			(1'b0),
	.dbg_lss_o			(),
	.dbg_is_o			(),
	.dbg_wp_o			(),
	.dbg_bp_o			(),

	.dbg_adr_i			(32'b0),      
	.dbg_we_i			(1'b0), 
	.dbg_stb_i			(1'b0),          
	.dbg_dat_i			(32'b0),
	.dbg_dat_o			(),
	.dbg_ack_o			(),
	
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
	.clk_i				(wb_clk),
	.rst_i				(wb_rst),
	
	.clmode_i			(2'b00),
	// Interrupts      
	.pic_ints_i			(or1200_pic_ints),
	.sig_tick(),

	.pm_cpustall_i			(1'b0));

   ////////////////////////////////////////////////////////////////////////
   //
   // Wishbone interconnect
   // 
   ////////////////////////////////////////////////////////////////////////
   wb_intercon wb_intercon0
     (.wb_clk_i         (wb_clk),
      .wb_rst_i         (wb_rst),
      // OR1200 Instruction bus (To Master)
      .wb_or1200_i_adr_i (wb_or1200_i_adr),
      .wb_or1200_i_dat_i (wb_or1200_i_dat),
      .wb_or1200_i_sel_i (wb_or1200_i_sel),
      .wb_or1200_i_we_i  (wb_or1200_i_we ),
      .wb_or1200_i_cyc_i (wb_or1200_i_cyc),
      .wb_or1200_i_stb_i (wb_or1200_i_stb),
      .wb_or1200_i_cti_i (wb_or1200_i_cti),
      .wb_or1200_i_bte_i (wb_or1200_i_bte),
      .wb_or1200_i_dat_o (wb_or1200_i_sdt),
      .wb_or1200_i_ack_o (wb_or1200_i_ack),
      .wb_or1200_i_err_o (wb_or1200_i_err),
      .wb_or1200_i_rty_o (wb_or1200_i_rty),
      // OR1200 Data bus (To Master)
      .wb_or1200_d_adr_i (wb_or1200_d_adr),
      .wb_or1200_d_dat_i (wb_or1200_d_dat),
      .wb_or1200_d_sel_i (wb_or1200_d_sel),
      .wb_or1200_d_we_i  (wb_or1200_d_we ),
      .wb_or1200_d_cyc_i (wb_or1200_d_cyc),
      .wb_or1200_d_stb_i (wb_or1200_d_stb),
      .wb_or1200_d_cti_i (wb_or1200_d_cti),
      .wb_or1200_d_bte_i (wb_or1200_d_bte),
      .wb_or1200_d_dat_o (wb_or1200_d_sdt),
      .wb_or1200_d_ack_o (wb_or1200_d_ack),
      .wb_or1200_d_err_o (wb_or1200_d_err),
      .wb_or1200_d_rty_o (wb_or1200_d_rty),
      // Memory Interface (To Slave)
      .wb_mem_adr_o      (wb_mem_adr),
      .wb_mem_dat_o      (wb_mem_dat),
      .wb_mem_sel_o      (wb_mem_sel),
      .wb_mem_we_o       (wb_mem_we),
      .wb_mem_cyc_o      (wb_mem_cyc),
      .wb_mem_stb_o      (wb_mem_stb),
      .wb_mem_cti_o      (wb_mem_cti),
      .wb_mem_bte_o      (wb_mem_bte),
      .wb_mem_dat_i      (wb_mem_sdt),
      .wb_mem_ack_i      (wb_mem_ack),
      .wb_mem_err_i      (wb_mem_err),
      .wb_mem_rty_i      (wb_mem_rty));
     
   ////////////////////////////////////////////////////////////////////////
   //
   // Generic main RAM
   // 
   ////////////////////////////////////////////////////////////////////////
   wb_bfm_memory #(.DEBUG (0),
		   .mem_size_bytes(32'h00800000))
   wb_bfm_memory0
     (
      //Wishbone Master interface
      .wb_clk_i (wb_clk),
      .wb_rst_i (wb_rst),
      .wb_adr_i	(wb_mem_adr),
      .wb_dat_i	(wb_mem_dat),
      .wb_sel_i	(wb_mem_sel),
      .wb_we_i	(wb_mem_we),
      .wb_cyc_i	(wb_mem_cyc),
      .wb_stb_i	(wb_mem_stb),
      .wb_cti_i	(wb_mem_cti),
      .wb_bte_i	(wb_mem_bte),
      .wb_sdt_o	(wb_mem_sdt),
      .wb_ack_o	(wb_mem_ack),
      .wb_err_o (wb_mem_err),
      .wb_rty_o (wb_mem_rty));
   

   ////////////////////////////////////////////////////////////////////////
   //
   // OR1200 Interrupt assignment
   // 
   ////////////////////////////////////////////////////////////////////////
   assign or1200_pic_ints[0] = 0; // Non-maskable inside OR1200
   assign or1200_pic_ints[1] = 0; // Non-maskable inside OR1200
   assign or1200_pic_ints[2] = 0;
   assign or1200_pic_ints[3] = 0;
   assign or1200_pic_ints[4] = 0;
   assign or1200_pic_ints[5] = 0;
   assign or1200_pic_ints[6] = 0;
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
   assign or1200_pic_ints[19] = 0;
   
endmodule
