module wb_bfm_memory
 #(//Wishbone parameters
   parameter dw = 32,
   parameter aw = 32,
   parameter DEBUG = 0,
   // Memory parameters
   parameter memory_file = "",
   parameter mem_size_bytes = 32'h0000_8000) // 32KBytes
  (input 	   wb_clk_i,
   input 	   wb_rst_i,
   
   input [aw-1:0]  wb_adr_i,
   input [dw-1:0]  wb_dat_i,
   input [3:0] 	   wb_sel_i,
   input 	   wb_we_i,
   input [1:0] 	   wb_bte_i,
   input [2:0] 	   wb_cti_i,
   input 	   wb_cyc_i,
   input 	   wb_stb_i,
   
   output 	   wb_ack_o,
   output 	   wb_err_o,
   output 	   wb_rty_o,
   output [dw-1:0] wb_sdt_o);

`include "wb_bfm_params.v"
   
   localparam bytes_per_dw = (dw/8);
   localparam mem_words = (mem_size_bytes/bytes_per_dw);   

   // synthesis attribute ram_style of mem is block
   reg [dw-1:0] 	mem [ 0 : mem_words-1 ]   /* verilator public */ /* synthesis ram_style = no_rw_check */;

   wb_bfm_slave
     #(.aw (aw))
   bfm0
     (.wb_clk   (wb_clk_i),
      .wb_rst   (wb_rst_i),
      .wb_adr_i (wb_adr_i),
      .wb_dat_i (wb_dat_i),
      .wb_sel_i (wb_sel_i),
      .wb_we_i  (wb_we_i), 
      .wb_cyc_i (wb_cyc_i),
      .wb_stb_i (wb_stb_i),
      .wb_cti_i (wb_cti_i),
      .wb_bte_i (wb_bte_i),
      .wb_sdt_o (wb_sdt_o),
      .wb_ack_o (wb_ack_o),
      .wb_err_o (wb_err_o),
      .wb_rty_o (wb_rty_o));

   reg [aw-1:0] 	address;
   reg [dw-1:0] 	data;
   
   always begin
      bfm0.init();
      address = bfm0.address; //Fetch start address

      while(bfm0.has_next) begin
	 //Set error on out of range accesses
	 if(address[31:2] > mem_words)
	   bfm0.error_response();
	 else begin
	    if(bfm0.op === WRITE) begin
	       bfm0.write_ack(data);
	       if(DEBUG) $display("%d : ram Write 0x%h = 0x%h %b", $time, address, data, bfm0.mask);
	       mem[address[31:2]] = data;
	    end else begin
	       if(DEBUG) $display("%d : ram Read  0x%h = 0x%h %b", $time, address, mem[address[31:2]], bfm0.mask);
	       bfm0.read_ack(mem[address[31:2]]);
	    end
	 end
	 if(bfm0.cycle_type === BURST_CYCLE)
	   address = bfm0.next_addr(address, bfm0.burst_type);
      end
   end

endmodule // wb_bfm_memory
