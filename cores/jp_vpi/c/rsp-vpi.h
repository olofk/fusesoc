/*$$HEADER*/
/******************************************************************************/
/*                                                                            */
/*                    H E A D E R   I N F O R M A T I O N                     */
/*                                                                            */
/******************************************************************************/

// Project Name                   : ORPSoCv2
// File Name                      : rsp-vpi.h
// Prepared By                    : jb, jb@orsoc.se
// Project Start                  : 2009-05-01

/*$$COPYRIGHT NOTICE*/
/******************************************************************************/
/*                                                                            */
/*                      C O P Y R I G H T   N O T I C E                       */
/*                                                                            */
/******************************************************************************/
/*
  This library is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public
  License as published by the Free Software Foundation; 
  version 2.1 of the License, a copy of which is available from
  http://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt.

  This library is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
  Lesser General Public License for more details.

  You should have received a copy of the GNU Lesser General Public
  License along with this library; if not, write to the Free Software
  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*/

// Defines for protocol ensuring synchronisation with the simulation process

// 1. rsp-rtl_sim will first write a command byte
// 2. rsp-rtl_sim will then send the address if it's a read or write
//    or the data to write if it's a dbg_cpu_wr_ctrl (stall & reset bits)
// 3. will then send data if we're writing and we sent address in 2
// 4. wait for response from vpi functions

// commands:
// 4'h1 jtag set instruction register (input: instruction value)
// 4'h2 set debug chain (dbg_set_command here) (input: chain value)
// 4'h3 cpu_ctrl_wr (input: ctrl value (2 bits))
// 4'h4 cpu_ctrl_rd (output: ctrl value (2bits))
// 4'h5 cpu wr reg (inputs: address, data)
// 4'h6 cpu rd reg (input: address; output: data)
// 4'h7 wb wr  (inputs: address, data, size)
// 4'h8 wb rd 32 (input: address; output: data)
// 4'h9 wb wr block 32 (inputs: address, length, data)
// 4'ha wb rd block 32 (inputs: address, length; output: data)
// 4'hb reset
// 4'hc read jtag id (output: data)
// 4'hd GDB detach - do something (like close down, restart, etc.)
// 4'he wb rd 8 (input: address, data pointer)
// There should be a correlating set of verilog `define's in the 
// verilog debug testbench module's include file, vpi_debug_defines.v

#define CMD_JTAG_SET_IR 0x1
#define CMD_SET_DEBUG_CHAIN 0x2
#define CMD_CPU_CTRL_WR 0x3
#define CMD_CPU_CTRL_RD 0x4
#define CMD_CPU_WR_REG 0x5
#define CMD_CPU_RD_REG 0x6
#define CMD_WB_WR 0x7
#define CMD_WB_RD32 0x8
#define CMD_WB_BLOCK_WR32 0x9
#define CMD_WB_BLOCK_RD32 0xa
#define CMD_RESET 0xb
#define CMD_READ_JTAG_ID 0xc
#define CMD_GDB_DETACH 0xd
#define CMD_WB_RD8 0xe
