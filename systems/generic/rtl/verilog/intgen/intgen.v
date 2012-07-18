/*
 *
 * Interrupt generation module
 * 
 * A counter is loaded with a value over the Wishbone bus interface, which then
 * counts down and issues an interrupt when the value is 1
 * 
 * 
 * Register 0 - write only - counter value
 * 
 * Register 1 - read/write - interrupt status/clear
 * 
 */

module intgen(
	      clk_i,
	      rst_i,
	      wb_adr_i,
	      wb_cyc_i,
	      wb_stb_i,
	      wb_dat_i,
	      wb_we_i,
	      wb_ack_o,
	      wb_dat_o,

	      irq_o
	      );


   input clk_i;
   input rst_i;
   
   input wb_adr_i;
   input wb_cyc_i;
   input wb_stb_i;
   input [7:0] wb_dat_i;
   input       wb_we_i;
   output      wb_ack_o;
   output [7:0] wb_dat_o;
   
   output reg 	irq_o;
   
   reg [7:0] 	counter;

   always @(posedge clk_i or posedge rst_i)
     if (rst_i)
       counter <= 0;
     else if (wb_stb_i & wb_cyc_i & wb_we_i & !wb_adr_i)
       // Write to adress 0 loads counter
       counter <= wb_dat_i;
     else if (|counter)
       counter <= counter - 1;
   
   always @(posedge clk_i or posedge rst_i)
     if (rst_i)
       irq_o <= 0;
     else if (wb_stb_i & wb_cyc_i & wb_we_i & wb_adr_i)
       // Clear on write to reg 1
       irq_o <= 0;
     else if (counter==8'd1)
       irq_o <= 1;

   assign wb_ack_o = wb_stb_i & wb_cyc_i;
   assign wb_dat_o = (wb_adr_i) ? {7'd0,irq_o} : counter;
   
endmodule // intgen

       

   