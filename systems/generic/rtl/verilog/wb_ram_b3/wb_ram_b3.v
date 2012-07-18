
// Version 5

//`define RANDOM_ACK_NEGATION

module wb_ram_b3(
		 wb_adr_i, wb_bte_i, wb_cti_i, wb_cyc_i, wb_dat_i, wb_sel_i,
		 wb_stb_i, wb_we_i,

		 wb_ack_o, wb_err_o, wb_rty_o, wb_dat_o,

		 wb_clk_i, wb_rst_i);

   // Memory parameters
   parameter dw = 32;

   // 32MB memory by default
   parameter aw = 23;
   parameter mem_size  = 8388608;

   input [aw-1:0]	wb_adr_i;
   input [1:0] 		wb_bte_i;
   input [2:0] 		wb_cti_i;
   input 		wb_cyc_i;
   input [dw-1:0] 	wb_dat_i;
   input [3:0] 		wb_sel_i;
   input 		wb_stb_i;
   input 		wb_we_i;
   
   output 		wb_ack_o;
   output 		wb_err_o;
   output 		wb_rty_o;
   output [dw-1:0] 	wb_dat_o;
   
   input 		wb_clk_i;
   input 		wb_rst_i;


   // synthesis attribute ram_style of mem is block
   reg [dw-1:0] 	mem [ 0 : mem_size-1 ]  /* verilator public */ /* synthesis ram_style = no_rw_check */;
   
   //reg [aw-1:2] wb_adr_i_r;
   reg [aw-1:0] adr;
   
   wire [31:0] 			   wr_data;

   // Register to indicate if the cycle is a Wishbone B3-registered feedback 
   // type access
   reg 				   wb_b3_trans;
   wire 			   wb_b3_trans_start, wb_b3_trans_stop;
   
   // Register to use for counting the addresses when doing burst accesses
   reg [aw-1:0]  burst_adr_counter;
   reg [2:0] 			   wb_cti_i_r;
   reg [1:0] 			   wb_bte_i_r;
   wire 			   using_burst_adr;
   wire 			   burst_access_wrong_wb_adr;

   reg 				   random_ack_negate;
   
   // Logic to detect if there's a burst access going on
   assign wb_b3_trans_start = ((wb_cti_i == 3'b001)|(wb_cti_i == 3'b010)) & 
			      wb_stb_i & !wb_b3_trans;
   
   assign  wb_b3_trans_stop = (wb_cti_i == 3'b111) & 
			      wb_stb_i & wb_b3_trans & wb_ack_o;
   
   always @(posedge wb_clk_i)
     if (wb_rst_i)
       wb_b3_trans <= 0;
     else if (wb_b3_trans_start)
       wb_b3_trans <= 1;
     else if (wb_b3_trans_stop)
       wb_b3_trans <= 0;

   // Burst address generation logic
   always @*
     if (wb_rst_i)
       burst_adr_counter = 0;
     else if (wb_b3_trans_start)
       burst_adr_counter = {2'b00,wb_adr_i[aw-1:2]};
     else if ((wb_cti_i_r == 3'b010) & wb_ack_o & wb_b3_trans)
       // Incrementing burst
       begin
	  if (wb_bte_i_r == 2'b00) // Linear burst
	    burst_adr_counter = adr + 1;
	  if (wb_bte_i_r == 2'b01) // 4-beat wrap burst
	    burst_adr_counter[1:0] = adr[1:0] + 1;
	  if (wb_bte_i_r == 2'b10) // 8-beat wrap burst
	    burst_adr_counter[2:0] = adr[2:0] + 1;
	  if (wb_bte_i_r == 2'b11) // 16-beat wrap burst
	    burst_adr_counter[3:0] = adr[3:0] + 1;
       end // if ((wb_cti_i_r == 3'b010) & wb_ack_o_r)
     else if (!wb_ack_o & wb_b3_trans)
	    burst_adr_counter = adr;


   always @(posedge wb_clk_i)
     wb_bte_i_r <= wb_bte_i;

   // Register it locally
   always @(posedge wb_clk_i)
     wb_cti_i_r <= wb_cti_i;

   assign using_burst_adr = wb_b3_trans;
   
   assign burst_access_wrong_wb_adr = (using_burst_adr & (adr != {2'b00,wb_adr_i[aw-1:2]}));

   // Address registering logic
   always@(posedge wb_clk_i)
     if(wb_rst_i)
       adr <= 0;
     else if (using_burst_adr)
       adr <= burst_adr_counter;
     else if (wb_cyc_i & wb_stb_i)
       adr <= {2'b00,wb_adr_i[aw-1:2]};
       
   parameter memory_file = "sram.vmem";

      
`ifdef verilator
   
   task do_readmemh;
      // verilator public
      $readmemh(memory_file, mem);
   endtask // do_readmemh
   
`else
   
   initial
     begin
	$readmemh(memory_file, mem);
     end
   
`endif // !`ifdef verilator

      
   // Function to access RAM (for use by Verilator).
   function [31:0] get_mem;
      // verilator public
      input [aw-1:0] 		addr;
      get_mem = mem[addr];
   endfunction // get_mem

   // Function to write RAM (for use by Verilator).
   function set_mem;
      // verilator public
      input [aw-1:0] 		addr;
      input [dw-1:0] 		data;
      mem[addr] = data;
   endfunction // set_mem


   assign wb_rty_o = 0;

   // mux for data to ram, RMW on part sel != 4'hf
   assign wr_data[31:24] = wb_sel_i[3] ? wb_dat_i[31:24] : wb_dat_o[31:24];
   assign wr_data[23:16] = wb_sel_i[2] ? wb_dat_i[23:16] : wb_dat_o[23:16];
   assign wr_data[15: 8] = wb_sel_i[1] ? wb_dat_i[15: 8] : wb_dat_o[15: 8];
   assign wr_data[ 7: 0] = wb_sel_i[0] ? wb_dat_i[ 7: 0] : wb_dat_o[ 7: 0];

   // Address logic
   /*
   always @(posedge wb_clk_i)
     begin 
	if (wb_rst_i)
	  wb_adr_i_r <= 0;
	else
	  if (wb_cyc_i & wb_stb_i)
	    wb_adr_i_r <= wb_adr_i[aw-1:2];
     end
    */
   
   wire ram_we;
   assign ram_we = wb_we_i & wb_ack_o;

   assign wb_dat_o = mem[adr];
    
   // Write logic
   always @ (posedge wb_clk_i)
     begin
	if (ram_we)
	  mem[adr] <= wr_data;
     end
   
   // Ack Logic
   reg wb_ack_o_r;

   assign wb_ack_o = wb_ack_o_r & wb_stb_i;
   
   always @(posedge wb_clk_i)
     if (wb_rst_i)
       begin
          wb_ack_o_r <= 1'b0;
       end
     else if (wb_cyc_i) // We have bus
       begin
	  if (wb_cti_i == 3'b111)
	    begin
	       // End of burst
	       if (wb_ack_o_r)
		 // ALWAYS de-assert ack after burst end
		 wb_ack_o_r <= 0;
	       else if (wb_stb_i & !random_ack_negate)
		 wb_ack_o_r <= 1;
	       else
		 wb_ack_o_r <= 0;
	    end
	  else if (wb_cti_i == 3'b000)
	    begin
	       // Classic cycle acks
	       if (wb_stb_i & !random_ack_negate)
		 begin
		    if (!wb_ack_o_r)
		      wb_ack_o_r <= 1;
		    else
		      wb_ack_o_r <= 0;
		 end
	       else
		 wb_ack_o_r <= 0;
	    end // if (wb_cti_i == 3'b000)
	  else if ((wb_cti_i == 3'b001) | (wb_cti_i == 3'b010))
	    begin
	       // Increment/constant address bursts
	       if (wb_stb_i & !random_ack_negate)
		 wb_ack_o_r <= 1;
	       else
		 wb_ack_o_r <= 0;
	    end
	  else if (wb_cti_i == 3'b111)
	    begin
	       // End of cycle
	       if (wb_stb_i & !random_ack_negate)
		 wb_ack_o_r <= 1;
	       else
		 wb_ack_o_r <= 0;
	    end
       end // if (wb_cyc_i)
     else
       wb_ack_o_r <= 0;
   
   assign wb_err_o = 1'b0;// wb_ack_o & (burst_access_wrong_wb_adr); // OR in other errors here


   // Random ACK negation logic
`ifdef RANDOM_ACK_NEGATION
   reg [31:0] lfsr;
   always @(posedge wb_clk_i)
     if (wb_rst_i)
       lfsr <= 32'h273e2d4a;
     else lfsr <= {lfsr[30:0], ~(lfsr[30]^lfsr[6]^lfsr[4]^lfsr[1]^lfsr[0])};

   always @(posedge wb_clk_i)
     random_ack_negate <= lfsr[26];   
   
`else
   always @(wb_rst_i)
     random_ack_negate = 0;
`endif
   
   
   
endmodule // wb_ram_b3_v2

