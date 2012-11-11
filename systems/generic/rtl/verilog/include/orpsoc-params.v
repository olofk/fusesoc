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
parameter uart0_wb_adr = 8'h90;
parameter uart0_aw = 3;

// Interrupt generator (intgen) params
parameter intgen_wb_adr = 8'he1;
parameter intgen_addr_width = 1;

// ROM
parameter rom0_dw = 32;
parameter rom0_aw = 6;

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

parameter ibus_slaves = 2;
parameter rom0_slave_nr     = 0;
parameter mc0_ibus_slave_nr = 1;

///////////////////////////
//                       //
// Data bus              //
//                       //
///////////////////////////
parameter dbus_slaves = 2;
parameter mc0_dbus_slave_nr = 0;
parameter bbus_slave_nr = 1;

///////////////////////////////
//                           //
// Byte-wide peripheral bus  //
//                           //
///////////////////////////////
parameter bbus_slaves = 2;
parameter uart_slave_nr = 0;
parameter intgen_slave_nr = 1;
