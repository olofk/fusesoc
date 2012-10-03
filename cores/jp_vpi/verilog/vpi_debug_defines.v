//////////////////////////////////////////////////////////////////////
////                                                              ////
////  ORPSoC Testbench                                            ////
////                                                              ////
////  Description                                                 ////
////  ORPSoC VPI Debugging Testbench defines file                 ////
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
// Defines from the following files:
// tap_defines.v

// Define IDCODE Value
`define IDCODE_VALUE  32'h14951185

// Length of the Instruction register
`define	IR_LENGTH	4

// Supported Instructions
`define EXTEST          4'b0000
`define SAMPLE_PRELOAD  4'b0001
`define IDCODE          4'b0010
`define DEBUG           4'b1000
`define MBIST           4'b1001
`define BYPASS          4'b1111

// Number of cells in boundary scan chain
`define BS_CELL_NB      32'd558

//dbg_defines.v

// Length of the MODULE ID register
`define	DBG_TOP_MODULE_ID_LENGTH	4

// Length of data
`define DBG_TOP_MODULE_DATA_LEN  `DBG_TOP_MODULE_ID_LENGTH + 1
`define DBG_TOP_DATA_CNT          3

// Length of status
`define DBG_TOP_STATUS_LEN        3'd4
`define DBG_TOP_STATUS_CNT_WIDTH  3

// Length of the CRC
`define	DBG_TOP_CRC_LEN           32
`define DBG_TOP_CRC_CNT           6

// Chains
`define DBG_TOP_WISHBONE_DEBUG_MODULE 4'h0
`define DBG_TOP_CPU0_DEBUG_MODULE     4'h1
`define DBG_TOP_CPU1_DEBUG_MODULE     4'h2

// dbg_wb_defines.v

// If WISHBONE sub-module is supported uncomment the folowing line
`define DBG_WISHBONE_SUPPORTED

// If CPU_0 sub-module is supported uncomment the folowing line
`define DBG_CPU0_SUPPORTED

// If CPU_1 sub-module is supported uncomment the folowing line
//`define DBG_CPU1_SUPPORTED

// If more debug info is needed, uncomment the follofing line
//`define DBG_MORE_INFO


// Defining length of the command
`define DBG_WB_CMD_LEN          3'd4
`define DBG_WB_CMD_CNT_WIDTH    3

// Defining length of the access_type field
`define DBG_WB_ACC_TYPE_LEN     3'd4

// Defining length of the address
`define DBG_WB_ADR_LEN          6'd32

// Defining length of the length register
`define DBG_WB_LEN_LEN          5'd16

// Defining total length of the DR needed
`define DBG_WB_DR_LEN           (`DBG_WB_ACC_TYPE_LEN + `DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN)

// Defining length of the CRC
`define DBG_WB_CRC_LEN          6'd32
`define DBG_WB_CRC_CNT_WIDTH    6

// Defining length of status
`define DBG_WB_STATUS_LEN       3'd4
`define DBG_WB_STATUS_CNT_WIDTH 3

// Defining length of the data
`define DBG_WB_DATA_CNT_WIDTH     (`DBG_WB_LEN_LEN + 3)
`define DBG_WB_DATA_CNT_LIM_WIDTH `DBG_WB_LEN_LEN

//Defining commands
`define DBG_WB_GO               4'h0
`define DBG_WB_RD_COMM          4'h1
`define DBG_WB_WR_COMM          4'h2

// Defining access types for wishbone
`define DBG_WB_WRITE8           4'h0
`define DBG_WB_WRITE16          4'h1
`define DBG_WB_WRITE32          4'h2
`define DBG_WB_READ8            4'h4
`define DBG_WB_READ16           4'h5
`define DBG_WB_READ32           4'h6

// dbg_cpu_defines.v


// Defining length of the command
`define DBG_CPU_CMD_LEN          3'd4
`define DBG_CPU_CMD_CNT_WIDTH    3

// Defining length of the access_type field
`define DBG_CPU_ACC_TYPE_LEN     3'd4

// Defining length of the address
`define DBG_CPU_ADR_LEN          6'd32

// Defining length of the length register
`define DBG_CPU_LEN_LEN          5'd16

// Defining total length of the DR needed
//define DBG_CPU_DR_LEN           (`DBG_CPU_ACC_TYPE_LEN + `DBG_CPU_ADR_LEN + `DBG_CPU_LEN_LEN)
`define DBG_CPU_DR_LEN           52
// Defining length of the CRC
`define DBG_CPU_CRC_LEN          6'd32
`define DBG_CPU_CRC_CNT_WIDTH    6

// Defining length of status
`define DBG_CPU_STATUS_LEN       3'd4
`define DBG_CPU_STATUS_CNT_WIDTH 3

// Defining length of the data
//define DBG_CPU_DATA_CNT_WIDTH      `DBG_CPU_LEN_LEN + 3
`define DBG_CPU_DATA_CNT_WIDTH    19
//define DBG_CPU_DATA_CNT_LIM_WIDTH   `DBG_CPU_LEN_LEN
`define DBG_CPU_DATA_CNT_LIM_WIDTH 16
// Defining length of the control register
`define DBG_CPU_CTRL_LEN         2

//Defining commands
`define DBG_CPU_GO               4'h0
`define DBG_CPU_RD_COMM          4'h1
`define DBG_CPU_WR_COMM          4'h2
`define DBG_CPU_RD_CTRL          4'h3
`define DBG_CPU_WR_CTRL          4'h4

// Defining access types for wishbone
`define DBG_CPU_WRITE            4'h2
`define DBG_CPU_READ             4'h6


// commands from jp_vpi
`define CMD_JTAG_SET_IR          4'h1
`define CMD_SET_DEBUG_CHAIN      4'h2
`define CMD_CPU_CTRL_WR          4'h3
`define CMD_CPU_CTRL_RD          4'h4
`define CMD_CPU_WR_REG           4'h5
`define CMD_CPU_RD_REG           4'h6
`define CMD_WB_WR                4'h7
`define CMD_WB_RD32              4'h8
`define CMD_WB_BLOCK_WR32        4'h9
`define CMD_WB_BLOCK_RD32        4'ha
`define CMD_RESET                4'hb
`define CMD_READ_JTAG_ID         4'hc
`define CMD_GDB_DETACH           4'hd
`define CMD_WB_RD8               4'he /* Byte read is useful with a system with byte peripherals! */
// commands:
// 4'h1 jtag set instruction register (input: instruction value)
// 4'h2 set debug chain (dbg_set_command here) (input: chain value)
// 4'h3 cpu_ctrl_wr (input: ctrl value (2 bits))
// 4'h4 cpu_ctrl_rd (output: ctrl value (2bits))
// 4'h5 cpu wr reg (inputs: address, data)
// 4'h6 cpu rd reg (input: address; output: data)
// 4'h7 wb wr (inputs: address, size, data)
// 4'h8 wb rd 32 (input: address; output: data)
// 4'h9 wb wr block 32 (inputs: address, length, data)
// 4'ha wb rd block 32 (inputs: address, length; output: data)
// 4'hb reset
// 4'hc read jtag id (output: data)

`define SDRAM_BASE_ADDRESS 32'h00000000
