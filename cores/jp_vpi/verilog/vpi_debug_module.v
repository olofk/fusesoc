//////////////////////////////////////////////////////////////////////
////                                                              ////
////  ORPSoC Testbench                                            ////
////                                                              ////
////  Description                                                 ////
////  ORPSoC VPI Debugging Testbench file                         ////
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
`timescale 1ns/10ps

`include "vpi_debug_defines.v"

// uncomment the following line to get more debug output for this module 
//`define DEBUG_INFO
//`define VPI_DEBUG_INFO

module vpi_debug_module(tms, tck, tdi, tdo);
   
   output               tms;
   output               tck;
   output               tdi;
   input                tdo;

   reg                  tms;
   reg                  tck;
   reg                  tdi;
   
   reg [31:0] 		in_data_le, in_data_be;
   reg [31:0] 		incoming_word;
   reg                  err;
   integer              i;
   
   reg [31:0] 		id;
   reg [31:0] 		npc;
   reg [31:0] 		ppc;
   reg [31:0] 		r1;
   reg [31:0] 		insn;
   reg [31:0] 		result;
   reg [31:0] 		tmp;
   
   reg [31:0] 		crc_out;
   reg [31:0] 		crc_in;
   wire                 crc_match_in;
   
   reg [`DBG_TOP_STATUS_LEN -1:0] status;
   reg [`DBG_WB_STATUS_LEN -1:0]  status_wb;
   reg [`DBG_CPU_STATUS_LEN -1:0] status_cpu;
   
   // Text used for easier debugging
   reg [199:0] 			  test_text;
   reg [`DBG_WB_CMD_LEN -1:0] 	  last_wb_cmd;
   reg [`DBG_CPU_CMD_LEN -1:0] 	  last_cpu_cmd;
   reg [199:0] 			  last_wb_cmd_text;
   reg [199:0] 			  last_cpu_cmd_text;
   
   reg [31:0] 			  data_storage [0:4095];   // Data storage (for write and read operations). 
   reg [18:0] 			  length_global;
   
   parameter 			  Tp    = 1;   
//parameter Tck   = 25;   // Clock half period (Clok period = 50 ns => 20 MHz)
   parameter 			  Tck   = 50;   // Clock half period (Clok period = 100 ns => 10 MHz)

   integer cmd;
   integer block_cmd_length;
   integer jtag_instn_val;
   integer set_chain_val;
   
   reg [1:0] cpu_ctrl_val; // two important bits for the ctrl reg
   reg [31:0] cmd_adr;
   reg [31:0]  cmd_size;
   reg [31:0] cmd_data;

   
   initial
     begin
	$display("JTAG debug module with VPI interface enabled\n");
	tck    <=#Tp 1'b0;
	tdi    <=#Tp 1'bz;
	tms    <=#Tp 1'b0;

	// Insert a #delay here because we need to
	// wait until the PC isn't pointing to flash anymore
	// (this is around 20k ns if the flash_crash boot code
	// is being booted from, else much bigger, around 10mil ns)
	
	#2_000 main;
	  
     end
   
   task main;
      begin
	 
	 id     <=#Tp 32'h00;
	 npc    <=#Tp 32'h00;
	 ppc    <=#Tp 32'h00;
	 insn   <=#Tp 32'h00;
	 result <=#Tp 32'h00;
	 err    <=#Tp 1'b0;
	 tmp    <=#Tp 32'h00;
	
	// execute some cycles
	 #50000;
	 
	 reset_tap;
	 goto_run_test_idle;

	 //$init_rsp_server();

	 while (1) begin
	   
	   // Check for incoming command
	   
	   // wait until a command is sent
	   // poll with a delay here
	   cmd = -1;
	
	   while (cmd == -1)
	     begin
		#1000 $check_for_command(cmd);
	     end

	    // now switch on the command
	    case (cmd)
	      
	      `CMD_RESET : // reset
		begin
		   
		   // call reset task
		   reset_tap;
		   // and put TAP into run_test_idle state
		   goto_run_test_idle;
		   
	       end	     
	      
	      `CMD_JTAG_SET_IR : // set jtag instruction register
		begin
		   
		   $get_command_data(jtag_instn_val);	     
		   
		   set_instruction(jtag_instn_val);
		   
	       end
	      `CMD_SET_DEBUG_CHAIN : // set debug chain
	       begin
		  
		  $get_command_data(set_chain_val);
		  
		  module_select(set_chain_val, 1'b0);   // {chain, gen_crc_err}

	       end
	     `CMD_CPU_CTRL_WR : // cpu CTRL write
	       begin

		  $get_command_data(cpu_ctrl_val);

		  debug_cpu_wr_ctrl(cpu_ctrl_val, "");

	       end

	     `CMD_CPU_CTRL_RD : // cpu CTRL read
	       begin
		  
		  debug_cpu_rd_ctrl(cpu_ctrl_val);

		  $return_command_data(4,cpu_ctrl_val);
		  
	       end

	     `CMD_CPU_WR_REG :
	       begin
		  
		  $get_command_address(cmd_adr);

		  $get_command_data(block_cmd_length);

		  $get_command_block_data(block_cmd_length, data_storage);
		  
		  if (block_cmd_length > 4)
		    cpu_write_block(cmd_adr, block_cmd_length);
		  else
		    begin
		       cmd_data = data_storage[0]; // Get the single word we'll write
		       cpu_write_32(cmd_data, cmd_adr,16'h3);
`ifdef VPI_DEBUG_INFO
		  $display("CPU reg write. adr: 0x%x (reg group: %d reg#: %d), val: 0x%x",
			   cmd_adr,cmd_adr[15:11], cmd_adr[10:0], cmd_data);
`endif
		    end
		  		  

		  
	       end
	     
	     `CMD_CPU_RD_REG :
	       begin

		  $get_command_address(cmd_adr);

		  $get_command_data(block_cmd_length); // Added 090901 --jb

		  /* Depending on size, issue a block or single read */
		  if (block_cmd_length > 4 )
		    cpu_read_block(cmd_adr, block_cmd_length);
		  else
		    cpu_read_32(cmd_data, cmd_adr, 16'h3);

		  
`ifdef VPI_DEBUG_INFO
		  if (cmd_size > 4 )
		    $display("CPU reg read. block adr: 0x%x (reg group: %d reg#: %d), num: %d",
				cmd_adr,cmd_adr[15:11], cmd_adr[10:0],  block_cmd_length);
		  else
		    $display("CPU reg read. adr: 0x%x (reg group: %d reg#: %d), val: 0x%x",
				cmd_adr,cmd_adr[15:11], cmd_adr[10:0], cmd_data);
`endif

		  
		  $return_command_block_data(block_cmd_length, data_storage);
		  
	       end
	     
	     `CMD_WB_WR :
	       begin
		  
		  $get_command_address(cmd_adr);

		  $get_command_data(cmd_size);

		  $get_command_data(cmd_data);

		  case (cmd_size)
		    4 :
		      begin
			 wb_write_32(cmd_data, cmd_adr, 16'h3);
		      end
		    2 :
		      begin
			 wb_write_16(cmd_data[15:0], cmd_adr, 16'h1);
		      end
		    1 :
		      begin
			 wb_write_8(cmd_data[7:0], cmd_adr, 16'h0);
		      end
		    default:
		      begin
			 $display("* vpi_debug_module: CMD_WB_WR size incorrect: %d\n", cmd_size);
		      end
		  endcase // case (cmd_size)
		  
	       end
	     
	     `CMD_WB_RD32 :
	       begin

		  $get_command_address(cmd_adr);

		  wb_read_32(cmd_data, cmd_adr, 16'h3);

		  $return_command_data(4,cmd_data);
		  
	       end

	     `CMD_WB_RD8 :
	       begin

		  $get_command_address(cmd_adr);

		  wb_read_8(cmd_data, cmd_adr, 16'h0);

		  $return_command_data(1,cmd_data);
		  
	       end
	     
	     `CMD_WB_BLOCK_WR32 :
	       begin

		  $get_command_address(cmd_adr);
		  
		  $get_command_data(block_cmd_length);

		  $get_command_block_data(block_cmd_length, data_storage);

		  wb_block_write_32(cmd_adr ,block_cmd_length);
		  
	       end
	      
	      `CMD_WB_BLOCK_RD32 :
		begin
		   
		   $get_command_address(cmd_adr);
		   
		   $get_command_data(block_cmd_length);

		   wb_block_read_32(cmd_adr, block_cmd_length);
		   
		   $return_command_block_data(block_cmd_length, data_storage);
		   
		end
	      
	      `CMD_READ_JTAG_ID :
		begin
		   
		   read_id_code(id);
		   
		   $return_command_data(4,id);
		   
		end
	      
	      `CMD_GDB_DETACH :
		begin

		   $display("(%t)(%m)Debugging client disconnected. Finishing simulation", $time);
		   
		   
		   $finish();
		   
		end
	     
	      default:
		begin
		   $display("Somehow got to the default case in the command case statement.");
		   $display("Command was: %x", cmd);
		   $display("Exiting...");

		   $finish();//shouldn't be here
		end
	      
	    endcase // case (cmd)
	    
	    // send back response, which is currently nothing
	    // but could be used to signal something
	    $return_response();
	    
	 end // while (1)
      end
      
   endtask // main

   

   // Receiving data and calculating input crc
   always @(posedge tck)
     begin
	in_data_be[31:1] <= #1 in_data_be[30:0];
	in_data_be[0]    <= #1 tdo;
	
	in_data_le[31]   <= #1 tdo;
	in_data_le[30:0] <= #1 in_data_le[31:1];
     end

   // Generation of the TCK signal
   task gen_clk;
      input [31:0] number;
      integer 	   i;
      begin
	 for(i=0; i<number; i=i+1)
	   begin
              #Tck tck<=1;
              #Tck tck<=0;
	   end
      end
   endtask

   // TAP reset
   task reset_tap;
      
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task reset_tap", $time);
`endif
	 tms<=#1 1'b1;
	 gen_clk(5);
      end
   endtask


   // Goes to RunTestIdle state
   task goto_run_test_idle;
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task goto_run_test_idle", $time);
`endif
	 tms<=#1 1'b0;
	 gen_clk(1);
      end
   endtask

   // sets the instruction to the IR register and goes to the RunTestIdle state
   task set_instruction;
      input [3:0] instr;
      integer 	  i;
      
      begin
`ifdef DEBUG_INFO
	 case (instr)
	   `EXTEST          : $display("(%0t) Task set_instruction (EXTEST)", $time); 
	   `SAMPLE_PRELOAD  : $display("(%0t) Task set_instruction (SAMPLE_PRELOAD)", $time); 
	   `IDCODE          : $display("(%0t) Task set_instruction (IDCODE)", $time);
	   `DEBUG           : $display("(%0t) Task set_instruction (DEBUG)", $time);
	   `MBIST           : $display("(%0t) Task set_instruction (MBIST)", $time);
	   `BYPASS          : $display("(%0t) Task set_instruction (BYPASS)", $time);
	   default
             begin
                $display("(%0t) Task set_instruction (Unsupported instruction !!!)", $time);
                $display("\tERROR: Unsupported instruction !!!", $time);
                $stop;
             end
	 endcase
`endif

	 tms<=#1 1;
	 gen_clk(2);
	 tms<=#1 0;
	 gen_clk(2);  // we are in shiftIR

	 for(i=0; i<`IR_LENGTH-1; i=i+1)
	   begin
	      tdi<=#1 instr[i];
	      gen_clk(1);
	   end
	 
	 tdi<=#1 instr[i]; // last shift
	 tms<=#1 1;        // going out of shiftIR
	 gen_clk(1);
	 tdi<=#1 'hz;    // tri-state
	 gen_clk(1);
	 tms<=#1 0;
	 gen_clk(1);       // we are in RunTestIdle
      end
   endtask


   // send 32 bits through the device
   task test_bypass;
      input  [31:0] in;
      output [31:0] out;
      integer 	    i;
      
      reg [31:0]    out;

      begin
	 tms<=#Tp 1;
	 gen_clk(1);
	 tms<=#Tp 0;
	 gen_clk(2);             // we are in shiftDR

	 for(i=31; i>=0; i=i-1)
	   begin
	      tdi<=#Tp in[i];
	      gen_clk(1);
	   end

	 tms<=#Tp 1;             // going out of shiftDR
	 gen_clk(1);

	 out <=#Tp in_data_be;
	 tdi<=#Tp 'hz;

	 gen_clk(1);
	 tms<=#Tp 0;
	 gen_clk(1);             // we are in RunTestIdle
      end
   endtask

   // Reads the ID code
   task read_id_code;
      output [31:0] code;
      reg [31:0]    code;
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task read_id_code", $time);
`endif

	 tms<=#1 1;
	 gen_clk(1);
	 tms<=#1 0;
	 gen_clk(2);  // we are in shiftDR
	 
	 tdi<=#1 0;
	 gen_clk(31);
	 
	 tms<=#1 1;        // going out of shiftIR
	 gen_clk(1);
	 
	 code = in_data_le;
	 
	 tdi<=#1 'hz; // tri-state
	 gen_clk(1);
	 tms<=#1 0;
	 gen_clk(1);       // we are in RunTestIdle
      end
   endtask

   // test bundary scan chain
   task test_bs;
      input  [31:0] in;
      output [31:0] out;
      integer 	    i;
      
      reg [31:0]    out;

      begin
	 tms<=#Tp 1;
	 gen_clk(1);
	 tms<=#Tp 0;
	 gen_clk(2);             // we are in shiftDR

	 for(i=31; i>=0; i=i-1)
	   begin
	      tdi<=#Tp in[i];
	      gen_clk(1);
	   end

	 gen_clk(`BS_CELL_NB-1);
	 tms<=#Tp 1;             // going out of shiftDR
	 gen_clk(1);

	 out <=#Tp in_data_be;

	 gen_clk(1);
	 tms<=#Tp 0;
	 gen_clk(1);             // we are in RunTestIdle
      end
   endtask



   // sets the selected scan chain and goes to the RunTestIdle state
   task module_select;
      input [`DBG_TOP_MODULE_ID_LENGTH -1:0]  data;
      input 				      gen_crc_err;
      integer 				      i;
      
      begin
`ifdef DEBUG_INFO
	 case (data)
	   `DBG_TOP_CPU1_DEBUG_MODULE : $display("(%0t) Task module_select (DBG_TOP_CPU1_DEBUG_MODULE, gen_crc_err=%0d)", $time, gen_crc_err);
	   `DBG_TOP_CPU0_DEBUG_MODULE : $display("(%0t) Task module_select (DBG_TOP_CPU0_DEBUG_MODULE, gen_crc_err=%0d)", $time, gen_crc_err);
	   `DBG_TOP_WISHBONE_DEBUG_MODULE : $display("(%0t) Task module_select (DBG_TOP_WISHBONE_DEBUG_MODULE gen_crc_err=%0d)", $time, gen_crc_err);
	   default               : $display("(%0t) Task module_select (ERROR!!! Unknown module selected)", $time);
	 endcase
`endif
	 
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR
	 
	 status = {`DBG_TOP_STATUS_LEN{1'b0}};    // Initialize status to all 0's
	 crc_out = {`DBG_TOP_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff    
	 tdi<=#1 1'b1; // module_select bit
	 calculate_crc(1'b1);
	 gen_clk(1);
	 
	 for(i=`DBG_TOP_MODULE_ID_LENGTH -1; i>=0; i=i-1) // Shifting module ID
	   begin
	      tdi<=#1 data[i];
	      calculate_crc(data[i]);
	      gen_clk(1);
	   end

	 for(i=`DBG_TOP_CRC_LEN -1; i>=0; i=i-1)
	   begin
	      if (gen_crc_err & (i==0))  // Generate crc error at last crc bit
		tdi<=#1 ~crc_out[i];   // error crc
	      else
		tdi<=#1 crc_out[i];    // ok crc
	      
	      gen_clk(1);
	   end
	 
	 tdi<=#1 1'hz;  // tri-state
	 
	 crc_in = {`DBG_TOP_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff
	 
	 for(i=`DBG_TOP_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating 1 clock to read out a status bit.
              status[i] = tdo;
	   end
	 
	 for(i=0; i<`DBG_TOP_CRC_LEN -1; i=i+1)
	   gen_clk(1);
	 
	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr
	 
	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
`ifdef DEBUG_INFO
              $stop;
`endif
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle

	 if (|status)
	   begin
              $write("(*E) (%0t) Module select error: ", $time);
              casex (status)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("Non-existing module selected !!!\n\n", $time);
		4'bxx1x : $display("Status[1] should be 1'b0 !!!\n\n", $time);
		4'bxxx1 : $display("Status[0] should be 1'b0 !!!\n\n", $time);
              endcase
`ifdef DEBUG_INFO
              $stop;
`endif
	   end
      end
   endtask   // module_select



   // 32-bit write to the wishbone
   task wb_write_32;
      input [31:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 data_storage[0] = data;
	 debug_wishbone_wr_comm(`DBG_WB_WRITE32, addr, length, 1'b0);
	 last_wb_cmd = `DBG_WB_WRITE32;  last_wb_cmd_text = "DBG_WB_WRITE32";
	 length_global = length + 1;
	 debug_wishbone_go(1'b0, 1'b0);
	 //debug_wishbone_go(1'b1, 1'b0); // maybe causes underrun/overrun error when wait for WB ready?
	 if (length>3)
	   $display("WARNING: Only first data word is stored for writting ( See module %m)");
      end
   endtask

   // block 32-bit write to the wishbone
   // presumes data is already in data_storage[]
   task wb_block_write_32;
				    
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      begin

	 debug_wishbone_wr_comm(`DBG_WB_WRITE32, addr, length-1, 1'b0);

	 last_wb_cmd = `DBG_WB_WRITE32;  last_wb_cmd_text = "DBG_WB_WRITE32";
	 
	 length_global = length; // number of bytes!
	 	 
	 debug_wishbone_go(1'b0, 1'b0);
	 
	 //debug_wishbone_go(1'b1, 1'b0); // maybe causes underrun/overrun error when wait for WB ready?
	 
      end
   endtask
   
   // 32-bit read from the wishbone
   task wb_read_32;

    output [31:0] data;

    input [`DBG_WB_ADR_LEN -1:0] addr;
    input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 debug_wishbone_wr_comm(`DBG_WB_READ32, addr, length, 1'b0);
	 last_wb_cmd = `DBG_WB_READ32;  last_wb_cmd_text = "DBG_WB_READ32";
	 length_global = length + 1;
	 //debug_wishbone_go(1'b0, 1'b0);
	 debug_wishbone_go(1'b1, 1'b0);
	 data = data_storage[0];
	 if (length>3)
	   $display("WARNING: Only first data word is stored for writting ( See module %m)");
      end
   endtask // wb_read_32

   // 8-bit read from the wishbone
   task wb_read_8;

    output [31:0] data;

    input [`DBG_WB_ADR_LEN -1:0] addr;
    input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 debug_wishbone_wr_comm(`DBG_WB_READ8, addr, length, 1'b0);
	 last_wb_cmd = `DBG_WB_READ8;  last_wb_cmd_text = "DBG_WB_READ8";
	 length_global = length + 1;
	 debug_wishbone_go(1'b1, 1'b0);
	 data = data_storage[0];
      end
   endtask // wb_read_8
   


   // block 32-bit read from the wishbone
   // assumes data will be stored into data_storage[]
   task wb_block_read_32;

    input [`DBG_WB_ADR_LEN -1:0] addr;
    input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 debug_wishbone_wr_comm(`DBG_WB_READ32, addr, length-1, 1'b0);

	 last_wb_cmd = `DBG_WB_READ32;  last_wb_cmd_text = "DBG_WB_READ32";
	 
	 length_global = length;
	 
	 //debug_wishbone_go(1'b0, 1'b0);
	 debug_wishbone_go(1'b1, 1'b0);
	 	 
      end
   endtask

				    
   // 16-bit write to the wishbone
   task wb_write_16;
      input [15:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 data_storage[0] = {data, 16'h0};
	 debug_wishbone_wr_comm(`DBG_WB_WRITE16, addr, length, 1'b0);
	 last_wb_cmd = `DBG_WB_WRITE16;  last_wb_cmd_text = "DBG_WB_WRITE16";
	 length_global = length + 1;
	 debug_wishbone_go(1'b0, 1'b0);
	 if (length>1)
	   $display("WARNING: Only first data half is stored for writting ( See module %m)");
      end
   endtask



   // 8-bit write to the wishbone
   task wb_write_8;
      input [7:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      begin
	 data_storage[0] = {data, 24'h0};
	 debug_wishbone_wr_comm(`DBG_WB_WRITE8, addr, length, 1'b0);
	 last_wb_cmd = `DBG_WB_WRITE8;  last_wb_cmd_text = "DBG_WB_WRITE8";
	 length_global = length + 1;
	 debug_wishbone_go(1'b0, 1'b0);
	 if (length>0)
	   $display("WARNING: Only first data byte is stored for writting ( See module %m)");
      end
   endtask



   task debug_wishbone_wr_comm;
      input [`DBG_WB_ACC_TYPE_LEN -1:0]   acc_type;
      input [`DBG_WB_ADR_LEN -1:0] 	  addr;
      input [`DBG_WB_LEN_LEN -1:0] 	  length;
      input                               gen_crc_err;
      integer                             i;
      reg [`DBG_WB_CMD_LEN -1:0] 	  command;
      
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_wishbone_wr_comm: ", $time);
`endif
	 
	 command = `DBG_WB_WR_COMM;
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR
	 
	 crc_out = {`DBG_WB_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff
	 
	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);
	 
	 for(i=`DBG_WB_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_WB_ACC_TYPE_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 acc_type[i]; // command
	      calculate_crc(acc_type[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_WB_ADR_LEN -1; i>=0; i=i-1)       // address
	   begin
	      tdi<=#1 addr[i];
	      calculate_crc(addr[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_WB_LEN_LEN -1; i>=0; i=i-1)       // length
	   begin
	      tdi<=#1 length[i];
	      calculate_crc(length[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_WB_CRC_LEN -1; i>=0; i=i-1)
	   begin
	      if (gen_crc_err & (i==0))  // Generate crc error at last crc bit
		tdi<=#1 ~crc_out[i];   // error crc
	      else
		tdi<=#1 crc_out[i];    // ok crc
	      
	      gen_clk(1);
	   end
	 
	 tdi<=#1 1'hz;
	 
	 crc_in = {`DBG_WB_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff
	 
	 for(i=`DBG_WB_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating clock to read out a status bit.
              status_wb[i] = tdo;
	   end
	 
	 if (|status_wb)
	   begin
              $write("(*E) (%0t) debug_wishbone_wr_comm error: ", $time);
              casex (status_wb)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("Unknown command !!!\n\n", $time);
		4'bxx1x : $display("WISHBONE error !!!\n\n", $time);
		4'bxxx1 : $display("Overrun/Underrun !!!\n\n", $time);
              endcase
`ifdef DEBUG_INFO
              $stop;
`endif
	   end
	 
	 
	 for(i=0; i<`DBG_WB_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end
	 
	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr
	 
	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
`ifdef DEBUG_INFO
              $stop;
`endif
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_wishbone_wr_comm



   task debug_wishbone_go;

      input         wait_for_wb_ready;
      input         gen_crc_err;
      integer 	    i;
      reg [4:0]     bit_pointer;
      integer       word_pointer;
      reg [31:0]    tmp_data;
      reg [`DBG_WB_CMD_LEN -1:0] command;
      
      
      begin
	 
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_wishbone_go (previous command was %0s): ", $time, last_wb_cmd_text);
`endif

	 command = `DBG_WB_GO;
	 word_pointer = 0;
	 
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR
	 
	 crc_out = {`DBG_WB_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff
	 
	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);
	 
	 for(i=`DBG_WB_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end
	 
	 // W R I T E
	 if (
	     (last_wb_cmd == `DBG_WB_WRITE8) | (last_wb_cmd == `DBG_WB_WRITE16) | 
	     (last_wb_cmd == `DBG_WB_WRITE32)
	     )  // When WB_WRITEx was previously activated, data needs to be shifted.
	   begin
              for (i=0; i<((length_global) << 3); i=i+1)
		begin
		   
		   if ((!(i%32)) && (i>0))
		     begin			
			word_pointer = word_pointer + 1;
		     end
		   
		   tmp_data = data_storage[word_pointer];		   
		   
		   bit_pointer = 31-i[4:0];
		   
		   tdi<=#1 tmp_data[bit_pointer];
		   
		   calculate_crc(tmp_data[bit_pointer]);
		   
		   gen_clk(1);

		end
	   end
	 
	 for(i=`DBG_WB_CRC_LEN -1; i>=1; i=i-1)
	   begin
	      tdi<=#1 crc_out[i];
	      gen_clk(1);
	   end
	 
	 if (gen_crc_err)  // Generate crc error at last crc bit
	   tdi<=#1 ~crc_out[0];   // error crc
	 else
	   tdi<=#1 crc_out[0];    // ok crc
	 
	 if (wait_for_wb_ready)
	   begin
              tms<=#1 1'b1;
              gen_clk(1);       // to exit1_dr. Last CRC is shifted on this clk
              tms<=#1 1'b0;
              gen_clk(1);       // to pause_dr
	      
              #2;             // wait a bit for tdo to activate
              while (tdo)     // waiting for wb to send "ready"
		begin
		   gen_clk(1);       // staying in pause_dr
		end
	      
              tms<=#1 1'b1;
              gen_clk(1);       // to exit2_dr
              tms<=#1 1'b0;
              gen_clk(1);       // to shift_dr
	   end
	 else
	   begin
              gen_clk(1);       // Last CRC is shifted on this clk
	   end
	 
	 
	 tdi<=#1 1'hz;

	 // R E A D
	 
	 crc_in = {`DBG_WB_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff
	 
	 if (
	     (last_wb_cmd == `DBG_WB_READ8) | (last_wb_cmd == `DBG_WB_READ16) | 
	     (last_wb_cmd == `DBG_WB_READ32)
	     )  // When WB_READx was previously activated, data needs to be shifted.
	   begin
	      
`ifdef DEBUG_INFO
              $display("\t\tGenerating %0d clocks to read %0d data bytes.", length_global<<3, length_global);
`endif
              word_pointer = 0; // Reset pointer
	      
              for (i=0; i<(length_global<<3); i=i+1)
		begin
		   
		   gen_clk(1);
		   
		   if (i[2:0] == 7)   // Latching data
			incoming_word = {incoming_word[23:0],in_data_be[7:0]};

		   if (i[4:0] == 31)
		     begin
			data_storage[word_pointer] = incoming_word;
`ifdef DEBUG_INFO
			$display("\t\tin_data_be = 0x%x", incoming_word);
`endif
			word_pointer = word_pointer + 1;
			
		     end
		end // for (i=0; i<(length_global<<3); i=i+1)
	      
	      // Copy in any leftovers
	      if (length_global[1:0] != 0)
		begin
		   data_storage[word_pointer] = incoming_word;
`ifdef DEBUG_INFO
		   $display("\t\tin_data_be = 0x%x", incoming_word);
`endif		   
		end
	   end
	 
	 for(i=`DBG_WB_STATUS_LEN -1; i>=0; i=i-1)
	   begin
	      
              gen_clk(1);     // Generating clock to read out a status bit.
              status_wb[i] = tdo;
	      
	   end
	 
	 if (|status_wb)
	   begin
              $write("(*E) (%0t) debug_wishbone_go error: ", $time);
              casex (status_wb)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("Unknown command !!!\n\n", $time);
		4'bxx1x : $display("WISHBONE error !!!\n\n", $time);
		4'bxxx1 : $display("Overrun/Underrun !!!\n\n", $time);
              endcase
`ifdef DEBUG_INFO
              $stop;
`endif
	   end
	 
	 
	 for(i=0; i<`DBG_WB_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end
	 
	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr
	 
	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
`ifdef DEBUG_INFO
              $stop;
`endif
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_wishbone_go



   task debug_cpu_wr_ctrl;
      input [`DBG_CPU_DR_LEN -1:0]  data;
      input [99:0] 		    text;
      integer                       i;
      reg [`DBG_CPU_CMD_LEN -1:0]   command;
      
      begin
	 test_text = text;
	 
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_cpu_wr_ctrl (data=0x%0x (%0s))", $time, data, text);
`endif
	 
	 command = `DBG_CPU_WR_CTRL;
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR
	 
	 crc_out = {`DBG_CPU_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff
	 
	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);
	 
	 for(i=`DBG_CPU_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end

	 
	 for(i=`DBG_CPU_CTRL_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 data[i];                                    // data (used cotrol bits
	      calculate_crc(data[i]);
	      gen_clk(1);
	   end

	 for(i=`DBG_CPU_DR_LEN - `DBG_CPU_CTRL_LEN -1; i>=0; i=i-1)  // unused control bits
	   begin
	      tdi<=#1 1'b0;
	      calculate_crc(1'b0);
	      gen_clk(1);
	   end
	 
	 
	 for(i=`DBG_CPU_CRC_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 crc_out[i];    // ok crc
	      gen_clk(1);
	   end
	 
	 tdi<=#1 1'hz;
	 
	 crc_in = {`DBG_CPU_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff
	 
	 for(i=`DBG_CPU_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating clock to read out a status bit.
              status_cpu[i] = tdo;
	   end
	 
	 if (|status_cpu)
	   begin
              $write("(*E) (%0t) debug_cpu_wr_ctrl error: ", $time);
              casex (status_cpu)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("??? error !!!\n\n", $time);
		4'bxx1x : $display("??? error !!!\n\n", $time);
		4'bxxx1 : $display("??? error !!!\n\n", $time);
              endcase
`ifdef DEBUG_INFO
              $stop;
`endif
	   end
	 
	 
	 for(i=0; i<`DBG_CPU_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end
	 
	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr
	 
	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
`ifdef DEBUG_INFO
              $stop;
`endif
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_cpu_wr_ctrl

   task debug_cpu_rd_ctrl;
      output [`DBG_CPU_DR_LEN -1:0]  data;
      //input [99:0] 		     text;
      integer 			     i;
      reg [`DBG_CPU_CMD_LEN -1:0]    command;
      
      begin

	 
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_cpu_rd_ctrl", $time);
`endif
	 
	 command = `DBG_CPU_RD_CTRL;
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR
	 
	 crc_out = {`DBG_CPU_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff
	 
	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);
	 
	 for(i=`DBG_CPU_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_CPU_CRC_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 crc_out[i];    // ok crc
	      gen_clk(1);
	   end
	 
	 tdi<=#1 1'hz;
	 
	 crc_in = {`DBG_CPU_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff
	 
	 // Read incoming debug ctrl data (52 bits)
	 //cpu_ctrl_val[1:0];
	 gen_clk(1);
	 //cpu_ctrl_val[0]  <= #1 tdo; // cpu reset bit
	 data[0]  <= #1 tdo; // cpu reset bit
	 gen_clk(1);
	 //cpu_ctrl_val[1]  <= #1 tdo; // cpu stall bit
	 data[1]  <= #1 tdo; // cpu stall bit
	 
	 for(i=`DBG_CPU_DR_LEN - `DBG_CPU_CTRL_LEN -1; i>=0; i=i-1)  // unused control bits
	   begin
	      gen_clk(1);
	   end     
	 
	 for(i=`DBG_CPU_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating clock to read out a status bit.
              status_cpu[i] = tdo;
	   end
	 
	 if (|status_cpu)
	   begin
              $write("(*E) (%0t) debug_cpu_wr_ctrl error: ", $time);
              casex (status_cpu)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("??? error !!!\n\n", $time);
		4'bxx1x : $display("??? error !!!\n\n", $time);
		4'bxxx1 : $display("??? error !!!\n\n", $time);
              endcase // casex (status_cpu)
	      
	   end
	 
	 
	 for(i=0; i<`DBG_CPU_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end
	 
	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr
	 
	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);

	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_cpu_rd_ctrl


   // 32-bit read from cpu
   task cpu_read_32;
      output [31:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      reg [31:0] 		   tmp;

      begin
	 debug_cpu_wr_comm(`DBG_CPU_READ, addr, length, 1'b0);
	 
	 last_cpu_cmd = `DBG_CPU_READ;  last_cpu_cmd_text = "DBG_CPU_READ";
	 
	 length_global = length + 1;
	 
	 debug_cpu_go(1'b0, 1'b0);
	 
	 data = data_storage[0];
	 
	 if (length>3)
	   $display("WARNING: Only first data word is returned( See module %m.)");
	 
      end
   endtask

   // block of 32-bit reads from cpu
   task cpu_read_block;
      //output [31:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      reg [31:0] 		   tmp;

      begin
	 debug_cpu_wr_comm(`DBG_CPU_READ, addr, length-1, 1'b0);
	 
	 last_cpu_cmd = `DBG_CPU_READ;  last_cpu_cmd_text = "DBG_CPU_READ";
	 
	 length_global = length;
	 
	 debug_cpu_go(1'b0, 1'b0);
	 
	 //data = data_storage[0];
	 
	 //if (length>3)
	 //  $display("WARNING: Only first data word is returned( See module %m.)");
	 
      end
   endtask


   // 32-bit write to cpu
   task cpu_write_32;
      input [31:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      reg [31:0] 		   tmp;

      begin
	 debug_cpu_wr_comm(`DBG_CPU_WRITE, addr, length, 1'b0);
	 last_cpu_cmd = `DBG_CPU_WRITE;  last_cpu_cmd_text = "DBG_CPU_WRITE";
	 length_global = length + 1;
	 data_storage[0] = data;
	 debug_cpu_go(1'b0, 1'b0);
	 if (length>3)
	   $display("WARNING: Only first data word is stored for writting ( See module %m)");
      end
   endtask

   // block of 32-bit writes to cpu
   // Data will already be in data_storage
   task cpu_write_block;
      //input [31:0] data;
      input [`DBG_WB_ADR_LEN -1:0] addr;
      input [`DBG_WB_LEN_LEN -1:0] length;

      reg [31:0] 		   tmp;

      begin
	 debug_cpu_wr_comm(`DBG_CPU_WRITE, addr, length-1, 1'b0);
	 last_cpu_cmd = `DBG_CPU_WRITE;  last_cpu_cmd_text = "DBG_CPU_WRITE";
	 length_global = length;
	 debug_cpu_go(1'b0, 1'b0);
      end
   endtask


   task debug_cpu_wr_comm;
      input [`DBG_CPU_ACC_TYPE_LEN -1:0]  acc_type;
      input [`DBG_CPU_ADR_LEN -1:0] 	  addr;
      input [`DBG_CPU_LEN_LEN -1:0] 	  length;
      input                               gen_crc_err;
      integer                             i;
      reg [`DBG_CPU_CMD_LEN -1:0] 	  command;
      
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_cpu_wr_comm: ", $time);
`endif

	 command = `DBG_CPU_WR_COMM;
	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR

	 crc_out = {`DBG_CPU_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff

	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);

	 for(i=`DBG_CPU_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end

	 for(i=`DBG_CPU_ACC_TYPE_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 acc_type[i]; // command
	      calculate_crc(acc_type[i]);
	      gen_clk(1);
	   end

	 for(i=`DBG_CPU_ADR_LEN -1; i>=0; i=i-1)       // address
	   begin
	      tdi<=#1 addr[i];
	      calculate_crc(addr[i]);
	      gen_clk(1);
	   end
	 
	 for(i=`DBG_CPU_LEN_LEN -1; i>=0; i=i-1)       // length
	   begin
	      tdi<=#1 length[i];
	      calculate_crc(length[i]);
	      gen_clk(1);
	   end

	 for(i=`DBG_CPU_CRC_LEN -1; i>=0; i=i-1)
	   begin
	      if (gen_crc_err & (i==0))      // Generate crc error at last crc bit
		tdi<=#1 ~crc_out[i];   // error crc
	      else
		tdi<=#1 crc_out[i];    // ok crc

	      gen_clk(1);
	   end

	 tdi<=#1 1'hz;

	 crc_in = {`DBG_CPU_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff

	 for(i=`DBG_CPU_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating clock to read out a status bit.
              status_cpu[i] = tdo;
	   end

	 if (|status_cpu)
	   begin
              $write("(*E) (%0t) debug_cpu_wr_comm error: ", $time);
              casex (status_cpu)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("Unknown command !!!\n\n", $time);
		4'bxx1x : $display("??? error !!!\n\n", $time);
		4'bxxx1 : $display("Overrun/Underrun !!!\n\n", $time);
              endcase
`ifdef DEBUG_INFO
              $stop;
`endif
	   end


	 for(i=0; i<`DBG_CPU_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr

	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
`ifdef DEBUG_INFO
              $stop;
`endif
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_cpu_wr_comm



   task debug_cpu_go;
      input         wait_for_cpu_ready;
      input         gen_crc_err;
      integer 	    i;
      reg [4:0]     bit_pointer;
      integer       word_pointer;
      reg [31:0]    tmp_data;
      reg [`DBG_CPU_CMD_LEN -1:0] command;

      
      begin
`ifdef DEBUG_INFO
	 $display("(%0t) Task debug_cpu_go (previous command was %0s): ", $time, last_cpu_cmd_text);
`endif
	 command = `DBG_CPU_GO;
	 word_pointer = 0;

	 tms<=#1 1'b1;
	 gen_clk(1);
	 tms<=#1 1'b0;
	 gen_clk(2);  // we are in shiftDR

	 crc_out = {`DBG_CPU_CRC_LEN{1'b1}}; // Initialize outgoing CRC to all ff

	 tdi<=#1 1'b0; // module_select bit = 0
	 calculate_crc(1'b0);
	 gen_clk(1);

	 for(i=`DBG_CPU_CMD_LEN -1; i>=0; i=i-1)
	   begin
	      tdi<=#1 command[i]; // command
	      calculate_crc(command[i]);
	      gen_clk(1);
	   end


	 if (last_cpu_cmd == `DBG_CPU_WRITE)  // When DBG_CPU_WRITE was previously activated, data needs to be shifted.
	   begin
              for (i=0; i<((length_global) << 3); i=i+1)
		begin
		   tmp_data = data_storage[word_pointer];
		   if ((!(i%32)) && (i>0))
		     begin
			word_pointer = word_pointer + 1;
		     end
		   bit_pointer = 31-i[4:0];
		   tdi<=#1 tmp_data[bit_pointer];
		   calculate_crc(tmp_data[bit_pointer]);
		   gen_clk(1);

		end
	   end

	 for(i=`DBG_CPU_CRC_LEN -1; i>=1; i=i-1)
	   begin
	      tdi<=#1 crc_out[i];
	      gen_clk(1);
	   end

	 if (gen_crc_err)  // Generate crc error at last crc bit
	   tdi<=#1 ~crc_out[0];   // error crc
	 else
	   tdi<=#1 crc_out[0];    // ok crc

	 if (wait_for_cpu_ready)
	   begin
              tms<=#1 1'b1;
              gen_clk(1);       // to exit1_dr. Last CRC is shifted on this clk
              tms<=#1 1'b0;
              gen_clk(1);       // to pause_dr

              #2;             // wait a bit for tdo to activate
              while (tdo)     // waiting for wb to send "ready"
		begin
		   gen_clk(1);       // staying in pause_dr
		end
	      
              tms<=#1 1'b1;
              gen_clk(1);       // to exit2_dr
              tms<=#1 1'b0;
              gen_clk(1);       // to shift_dr
	   end
	 else
	   begin
              gen_clk(1);       // Last CRC is shifted on this clk
	   end


	 tdi<=#1 1'hz;
	 crc_in = {`DBG_CPU_CRC_LEN{1'b1}};  // Initialize incoming CRC to all ff

	 if (last_cpu_cmd == `DBG_CPU_READ)  // When DBG_CPU_READ was previously activated, data needs to be shifted.
	   begin
`ifdef DEBUG_INFO
              $display("\t\tGenerating %0d clocks to read %0d data bytes.", length_global<<3, length_global);
`endif
              word_pointer = 0; // Reset pointer
              for (i=0; i<(length_global<<3); i=i+1)
		begin
		   
		   gen_clk(1);
		   
		   if (i[4:0] == 31)   // Latching data
		     begin
			data_storage[word_pointer] = in_data_be;
`ifdef DEBUG_INFO
			$display("\t\tin_data_be = 0x%x", in_data_be);
`endif
			word_pointer = word_pointer + 1;
		     end
		   
		end
	   end


	 for(i=`DBG_CPU_STATUS_LEN -1; i>=0; i=i-1)
	   begin
              gen_clk(1);     // Generating clock to read out a status bit.
              status_cpu[i] = tdo;
	   end

	 if (|status_cpu)
	   begin
              $write("(*E) (%0t) debug_cpu_go error: ", $time);
              casex (status_cpu)
		4'b1xxx : $display("CRC error !!!\n\n", $time);
		4'bx1xx : $display("Unknown command !!!\n\n", $time);
		4'bxx1x : $display("??? error !!!\n\n", $time);
		4'bxxx1 : $display("Overrun/Underrun !!!\n\n", $time);
              endcase
              $stop;
	   end


	 for(i=0; i<`DBG_CPU_CRC_LEN -1; i=i+1)  // Getting in the CRC
	   begin
	      gen_clk(1);
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to exit1_dr

	 if (~crc_match_in)
	   begin
              $display("(%0t) Incoming CRC failed !!!", $time);
              $stop;
	   end

	 tms<=#1 1'b1;
	 gen_clk(1);         // to update_dr
	 tms<=#1 1'b0;
	 gen_clk(1);         // to run_test_idle
      end
   endtask       // debug_cpu_go




   // Calculating outgoing CRC
   task calculate_crc;
      input data;
      
      begin
	 crc_out[0]  <= #1 data          ^ crc_out[31];
	 crc_out[1]  <= #1 data          ^ crc_out[0]  ^ crc_out[31];
	 crc_out[2]  <= #1 data          ^ crc_out[1]  ^ crc_out[31];
	 crc_out[3]  <= #1 crc_out[2];
	 crc_out[4]  <= #1 data          ^ crc_out[3]  ^ crc_out[31];
	 crc_out[5]  <= #1 data          ^ crc_out[4]  ^ crc_out[31];
	 crc_out[6]  <= #1 crc_out[5];
	 crc_out[7]  <= #1 data          ^ crc_out[6]  ^ crc_out[31];
	 crc_out[8]  <= #1 data          ^ crc_out[7]  ^ crc_out[31];
	 crc_out[9]  <= #1 crc_out[8];
	 crc_out[10] <= #1 data         ^ crc_out[9]  ^ crc_out[31];
	 crc_out[11] <= #1 data         ^ crc_out[10] ^ crc_out[31];
	 crc_out[12] <= #1 data         ^ crc_out[11] ^ crc_out[31];
	 crc_out[13] <= #1 crc_out[12];
	 crc_out[14] <= #1 crc_out[13];
	 crc_out[15] <= #1 crc_out[14];
	 crc_out[16] <= #1 data         ^ crc_out[15] ^ crc_out[31];
	 crc_out[17] <= #1 crc_out[16];
	 crc_out[18] <= #1 crc_out[17];
	 crc_out[19] <= #1 crc_out[18];
	 crc_out[20] <= #1 crc_out[19];
	 crc_out[21] <= #1 crc_out[20];
	 crc_out[22] <= #1 data         ^ crc_out[21] ^ crc_out[31];
	 crc_out[23] <= #1 data         ^ crc_out[22] ^ crc_out[31];
	 crc_out[24] <= #1 crc_out[23];
	 crc_out[25] <= #1 crc_out[24];
	 crc_out[26] <= #1 data         ^ crc_out[25] ^ crc_out[31];
	 crc_out[27] <= #1 crc_out[26];
	 crc_out[28] <= #1 crc_out[27];
	 crc_out[29] <= #1 crc_out[28];
	 crc_out[30] <= #1 crc_out[29];
	 crc_out[31] <= #1 crc_out[30];
      end
   endtask // calculate_crc


   // Calculating and checking input CRC
   always @(posedge tck)
     begin
	crc_in[0]  <= #1 tdo           ^ crc_in[31];
	crc_in[1]  <= #1 tdo           ^ crc_in[0]  ^ crc_in[31];
	crc_in[2]  <= #1 tdo           ^ crc_in[1]  ^ crc_in[31];
	crc_in[3]  <= #1 crc_in[2];
	crc_in[4]  <= #1 tdo           ^ crc_in[3]  ^ crc_in[31];
	crc_in[5]  <= #1 tdo           ^ crc_in[4]  ^ crc_in[31];
	crc_in[6]  <= #1 crc_in[5];
	crc_in[7]  <= #1 tdo           ^ crc_in[6]  ^ crc_in[31];
	crc_in[8]  <= #1 tdo           ^ crc_in[7]  ^ crc_in[31];
	crc_in[9]  <= #1 crc_in[8];
	crc_in[10] <= #1 tdo          ^ crc_in[9]  ^ crc_in[31];
	crc_in[11] <= #1 tdo          ^ crc_in[10] ^ crc_in[31];
	crc_in[12] <= #1 tdo          ^ crc_in[11] ^ crc_in[31];
	crc_in[13] <= #1 crc_in[12];
	crc_in[14] <= #1 crc_in[13];
	crc_in[15] <= #1 crc_in[14];
	crc_in[16] <= #1 tdo          ^ crc_in[15] ^ crc_in[31];
	crc_in[17] <= #1 crc_in[16];
	crc_in[18] <= #1 crc_in[17];
	crc_in[19] <= #1 crc_in[18];
	crc_in[20] <= #1 crc_in[19];
	crc_in[21] <= #1 crc_in[20];
	crc_in[22] <= #1 tdo          ^ crc_in[21] ^ crc_in[31];
	crc_in[23] <= #1 tdo          ^ crc_in[22] ^ crc_in[31];
	crc_in[24] <= #1 crc_in[23];
	crc_in[25] <= #1 crc_in[24];
	crc_in[26] <= #1 tdo          ^ crc_in[25] ^ crc_in[31];
	crc_in[27] <= #1 crc_in[26];
	crc_in[28] <= #1 crc_in[27];
	crc_in[29] <= #1 crc_in[28];
	crc_in[30] <= #1 crc_in[29];
	crc_in[31] <= #1 crc_in[30];
     end
   
   assign crc_match_in = crc_in == 32'h0;


endmodule // vpi_debug_module
