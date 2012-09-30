//////////////////////////////////////////////////////////////////////
////                                                              ////
////  ORPSoC Testbench UART Decoder                               ////
////                                                              ////
////  Description                                                 ////
////  ORPSoC Testbench UART output decoder                        ////
////                                                              ////
////  To Do:                                                      ////
////                                                              ////
////                                                              ////
////  Author(s):                                                  ////
////      - jb, jb@orsoc.se                                       ////
////                                                              ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2009 Authors and OPENCORES.ORG                 ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////

// Receieves and decodes 8-bit,  1 stop bit, no parity UART signals.
`timescale 1ns/1ns
module uart_decoder(clk, uart_tx);

   input clk;   
   input uart_tx;

   // Default baud of 115200, period (ns)
   parameter uart_baudrate_period_ns = 8680; 

   // Something to trigger the task
   always @(posedge clk)
     uart_decoder;
   
   task uart_decoder;
      reg [7:0] tx_byte;
      begin
	 while (uart_tx !== 1'b1)
	   @(uart_tx); 
	 // Wait for start bit
	 while (uart_tx !== 1'b0)
           @(uart_tx);
	 #(uart_baudrate_period_ns+(uart_baudrate_period_ns/2));
	 tx_byte[0] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[1] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[2] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[3] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[4] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[5] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[6] = uart_tx;
	 #uart_baudrate_period_ns;
	 tx_byte[7] = uart_tx;
	 #uart_baudrate_period_ns;
	 //Check for stop bit
	 if (uart_tx !== 1'b1)
	   begin
	      // Wait for return to idle
	      while (uart_tx !== 1'b1)
		@(uart_tx);
	   end
	 // display the char
	 $write("%c", tx_byte);
      end
   endtask // user_uart_read_byte

endmodule // uart_decoder
