//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_wb_defines.v                                            ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC Debug Interface.               ////
////  http://www.opencores.org/projects/DebugInterface/           ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////                                                              ////
////                                                              ////
////  All additional information is avaliable in the README.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2004 Authors                            ////
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
//
// CVS Revision History
//
// $Log: dbg_wb_defines.v,v $
// Revision 1.7  2004/03/31 14:34:08  igorm
// data_cnt_lim length changed to reduce number of warnings.
//
// Revision 1.6  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.5  2004/03/22 16:35:46  igorm
// Temp version before changing dbg interface.
//
// Revision 1.4  2004/01/16 14:51:33  mohor
// cpu registers added.
//
// Revision 1.3  2004/01/08 17:53:36  mohor
// tmp version.
//
// Revision 1.2  2004/01/06 17:15:19  mohor
// temp3 version.
//
// Revision 1.1  2003/12/23 15:09:04  mohor
// New directory structure. New version of the debug interface.
//
//
//

// Defining length of the command
`define DBG_WB_CMD_LEN          3'd4
`define DBG_WB_CMD_LEN_INT      4
`define DBG_WB_CMD_CNT_WIDTH    3

// Defining length of the access_type field
`define DBG_WB_ACC_TYPE_LEN     4


// Defining length of the address
`define DBG_WB_ADR_LEN          32

// Defining length of the length register
`define DBG_WB_LEN_LEN          16

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


