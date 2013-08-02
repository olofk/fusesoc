module wb_bfm_master
  #(parameter aw = 32,
    parameter dw = 32,
    parameter MAX_BURST_LENGTH = 32)
   (
    input 		wb_clk_i,
    input 		wb_rst_i,
    output reg [aw-1:0] wb_adr_o,
    output reg [dw-1:0] wb_dat_o,
    output reg [3:0] 	wb_sel_o,
    output reg 		wb_we_o,
    output reg 		wb_cyc_o,
    output reg 		wb_stb_o,
    output reg [2:0] 	wb_cti_o,
    output reg [1:0] 	wb_bte_o,
    input [dw-1:0] 	wb_sdt_i,
    input 		wb_ack_i,
    input 		wb_err_i,
    input 		wb_rty_i);

`include "wb_bfm_common.v"

   localparam Tp = 1;
   
   reg [aw-1:0]    addr;
   reg [31:0] 	   index = 0;
   reg [dw-1:0]    data = {dw{1'b0}};
   reg [3:0] 	   mask;
   reg 		   op;
   
   reg 		   cycle_type;
   reg [2:0] 	   burst_type;
   reg [31:0] 	   burst_length;

   task reset;
      begin
	 wb_adr_o = {aw{1'b0}};
	 wb_dat_o = {dw{1'b0}};
	 wb_sel_o = 4'h0;
	 wb_we_o = 1'b0;
	 wb_cyc_o = 1'b0;
	 wb_stb_o = 1'b0;
	 wb_cti_o = 3'b000;
	 wb_bte_o = 2'b00;
      end
   endtask
   
   task write;
      input [aw-1:0] addr_i;
      input [dw-1:0] data_i;
      input [3:0]    mask_i;
      
      output 	     err_o;
      
      begin
	 addr = addr_i;
	 data = data_i;
	 mask = mask_i;
	 
	 cycle_type = CLASSIC_CYCLE;
	 op = WRITE;
	 
	 init;
	 @(posedge wb_clk_i);
	 wait_for_ack;
	 err_o = wb_err_i;
      end
   endtask //

   task write_burst;
      input [aw-1:0] addr_i;
      input [dw*MAX_BURST_LENGTH-1:0] data_i;
      input [3:0] 		      mask_i;
      
      input [31:0] 		      burst_length_i;
      input [2:0] 		      burst_type_i;
      output 			      err_o;
      
      integer 			      idx;
      
      begin
	 addr = addr_i;
	 mask = mask_i;

	 op = WRITE;
	 
	 burst_length = burst_length_i;
	 
	 cycle_type = BURST_CYCLE;
	 burst_type = burst_type_i;
	 index = 0;

	 init;
	 
	 while(index < burst_length) begin
	    data = data_i[index*dw+:dw];
	    next;
	    addr = next_addr(addr, burst_type);
	    
	    index = index + 1;
	    
	 end
	 wb_cyc_o <= #Tp 1'b0;
	 wb_stb_o <= #Tp 1'b0;
	 wb_we_o  <= #Tp 1'b0;
	 wb_cti_o <= #Tp 3'b000;
	 //last;
	 
      end
   endtask

   task read_burst;
      input [aw-1:0] addr_i;
      output [dw*MAX_BURST_LENGTH-1:0] data_o;
      input [3:0] 		      mask_i;
      
      input [31:0] 		      burst_length_i;
      input [2:0] 		      burst_type_i;
      output 			      err_o;
      
      integer 			      idx;
      
      begin
	 
	 addr = addr_i;
	 mask = mask_i;

	 op = READ;
	 
	 burst_length = burst_length_i;
	 
	 cycle_type = BURST_CYCLE;
	 burst_type = burst_type_i;
	 index = 0;

	 init;
	 
	 while(index < burst_length) begin
	    next;
	    data_o[index*dw+:dw] = data;
	    addr = next_addr(addr, burst_type);
	    
	    index = index + 1;
	    
	 end
	 wb_cyc_o <= #Tp 1'b0;
	 wb_stb_o <= #Tp 1'b0;
	 wb_cti_o <= #Tp 3'b000;
	 
	 //last;
	 
      end
   endtask
   
   //Low level tasks
   task init;
      begin
	 if(wb_rst_i !== 1'b0) begin
	    @(negedge wb_rst_i);
	    @(posedge wb_clk_i);
	 end
	    
	 wb_sel_o <= #Tp mask;
	 wb_we_o  <= #Tp op;
	 wb_cyc_o <= #Tp 1'b1;

	 if(cycle_type == CLASSIC_CYCLE) begin
	    wb_cti_o <= #Tp 3'b000;
	    wb_bte_o <= #Tp 2'b00;
	 end else if(index == burst_length-1) begin
	    wb_cti_o <= #Tp 3'b111;
	    wb_bte_o <= #Tp 2'b00;
	 end else if(cycle_type == CONSTANT_BURST) begin
	    wb_cti_o <= #Tp 3'b001;
	    wb_bte_o <= #Tp 2'b00;
	 end else begin
	    wb_cti_o <=# Tp 3'b010;
	    wb_bte_o <=# Tp burst_type[1:0];
	 end
      end
   endtask

   task next;
      begin
	 wb_adr_o <= #Tp addr;
	 wb_dat_o <= #Tp (op === WRITE) ? data : {dw{1'b0}};
	 wb_stb_o <= #Tp 1'b1; //FIXME: Add wait states

	 if(cycle_type == CLASSIC_CYCLE) begin
	    while (wb_ack_i !== 1'b1)
	      @(posedge wb_clk_i);
	    data = wb_sdt_i;
	    wb_stb_o <= #Tp 1'b0;
	    @(negedge wb_ack_i);
	 end else begin
	    
	    if(index == burst_length-1)
	      wb_cti_o <= #Tp 3'b111;
	    
	    @(posedge wb_clk_i);
	    while(wb_ack_i !== 1'b1)
	      @(posedge wb_clk_i);
	    data = wb_sdt_i;
	 end
      end
   endtask // while

   task wait_for_ack;
      begin
	 if(cycle_type == CLASSIC_CYCLE) begin
	 end
      end
   endtask // if
   
endmodule
	    
