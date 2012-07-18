//////////////////////////////////////////////////////////////////////
////                                                              ////
//// orpsoc-params                                                ////
////                                                              ////
//// Top level ORPSoC parameters file                             ////
////                                                              ////
//// Included in toplevel and testbench                           ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2009, 2010 Authors and OPENCORES.ORG           ////
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

///////////////////////////
//                       //
// Peripheral parameters //
//                       //
///////////////////////////

// UART 0 params
parameter wbs_d_uart0_data_width = 8;
parameter uart0_wb_adr = 8'h90;
parameter uart0_data_width = 8;
parameter uart0_addr_width = 3;

// Interrupt generator (intgen) params
parameter intgen_wb_adr = 8'he1;
parameter intgen_data_width = 8;
parameter intgen_addr_width = 1;

// ROM
parameter wbs_i_rom0_data_width = 32;
parameter wbs_i_rom0_addr_width = 6;
parameter rom0_wb_adr = 4'hf;

//////////////////////////////////////////////////////
//                                                  //
// Wishbone bus parameters                          //
//                                                  //
//////////////////////////////////////////////////////

////////////////////////
//                    //
// Arbiter parameters //
//                    // 
////////////////////////

parameter wb_dw = 32; // Default Wishbone full word width
parameter wb_aw = 32; // Default Wishbone full address width

///////////////////////////
//                       //
// Instruction bus       //
//                       //
///////////////////////////
parameter ibus_arb_addr_match_width = 4;
// Slave addresses
parameter ibus_arb_slave0_adr = rom0_wb_adr; // ROM
parameter ibus_arb_slave1_adr = 4'h0;        // Main memory

///////////////////////////
//                       //
// Data bus              //
//                       //
///////////////////////////
// Has auto foward to last slave when no address hits
parameter dbus_arb_wb_addr_match_width = 8;
parameter dbus_arb_wb_num_slaves = 2;
// Slave addresses
parameter dbus_arb_slave0_adr = 4'h0; // Main memory (SDRAM/FPGA SRAM)
parameter dbus_arb_slave1_adr = 8'hxx; // Default slave - address don't care (X)

///////////////////////////////
//                           //
// Byte-wide peripheral bus  //
//                           //
///////////////////////////////
parameter bbus_arb_wb_addr_match_width = 8;
parameter bbus_arb_wb_num_slaves = 2; // Update this when changing slaves!
// Slave addresses
parameter bbus_arb_slave0_adr  = uart0_wb_adr;
parameter bbus_arb_slave1_adr  = intgen_wb_adr;
parameter bbus_arb_slave2_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave3_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave4_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave5_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave6_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave7_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave8_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave9_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave10_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave11_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave12_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave13_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave14_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave15_adr = 0 /* UNASSIGNED */;
parameter bbus_arb_slave16_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave17_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave18_adr  = 0 /* UNASSIGNED */;
parameter bbus_arb_slave19_adr  = 0 /* UNASSIGNED */;




