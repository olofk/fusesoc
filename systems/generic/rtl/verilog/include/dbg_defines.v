//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_defines.v                                               ////
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
// $Log: dbg_defines.v,v $
// Revision 1.20  2004/04/01 11:56:59  igorm
// Port names and defines for the supported CPUs changed.
//
// Revision 1.19  2004/03/28 20:27:02  igorm
// New release of the debug interface (3rd. release).
//
// Revision 1.18  2004/03/22 16:35:46  igorm
// Temp version before changing dbg interface.
//
// Revision 1.17  2004/01/30 10:24:30  mohor
// Defines WISHBONE_SUPPORTED and CPU_SUPPORTED added. By default both are
// turned on.
//
// Revision 1.16  2004/01/20 14:23:45  mohor
// Define name changed.
//
// Revision 1.15  2003/12/23 15:07:34  mohor
// New directory structure. New version of the debug interface.
// Files that are not needed removed.
//
// Revision 1.14  2003/10/23 16:17:00  mohor
// CRC logic changed.
//
// Revision 1.13  2003/10/21 09:48:31  simons
// Mbist support added.
//
// Revision 1.12  2003/09/17 14:38:57  simons
// WB_CNTL register added, some syncronization fixes.
//
// Revision 1.11  2003/08/28 13:55:21  simons
// Three more chains added for cpu debug access.
//
// Revision 1.10  2003/07/31 12:19:49  simons
// Multiple cpu support added.
//
// Revision 1.9  2002/05/07 14:43:59  mohor
// mon_cntl_o signals that controls monitor mux added.
//
// Revision 1.8  2002/01/25 07:58:34  mohor
// IDCODE bug fixed, chains reused to decreas size of core. Data is shifted-in
// not filled-in. Tested in hw.
//
// Revision 1.7  2001/12/06 10:08:06  mohor
// Warnings from synthesys tools fixed.
//
// Revision 1.6  2001/11/28 09:38:30  mohor
// Trace disabled by default.
//
// Revision 1.5  2001/10/15 09:55:47  mohor
// Wishbone interface added, few fixes for better performance,
// hooks for boundary scan testing added.
//
// Revision 1.4  2001/09/24 14:06:42  mohor
// Changes connected to the OpenRISC access (SPR read, SPR write).
//
// Revision 1.3  2001/09/20 10:11:25  mohor
// Working version. Few bugs fixed, comments added.
//
// Revision 1.2  2001/09/18 14:13:47  mohor
// Trace fixed. Some registers changed, trace simplified.
//
// Revision 1.1.1.1  2001/09/13 13:49:19  mohor
// Initial official release.
//
// Revision 1.3  2001/06/01 22:22:35  mohor
// This is a backup. It is not a fully working version. Not for use, yet.
//
// Revision 1.2  2001/05/18 13:10:00  mohor
// Headers changed. All additional information is now avaliable in the README.txt file.
//
// Revision 1.1.1.1  2001/05/18 06:35:08  mohor
// Initial release
//
//


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

// If WISHBONE sub-module is supported uncomment the folowing line
`define DBG_WISHBONE_SUPPORTED

// If CPU_0 sub-module is supported uncomment the folowing line
`define DBG_CPU0_SUPPORTED

// If CPU_1 sub-module is supported uncomment the folowing line
//`define DBG_CPU1_SUPPORTED

// If more debug info is needed, uncomment the follofing line
//`define DBG_MORE_INFO

