/*$$HEADER*/
/******************************************************************************/
/*                                                                            */
/*                    H E A D E R   I N F O R M A T I O N                     */
/*                                                                            */
/******************************************************************************/

// Project Name                   : ORPSoCv2
// File Name                      : gdb.h
// Prepared By                    : jb, rmd
// Project Start                  : 2008-10-01

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

/*$$CHANGE HISTORY*/
/******************************************************************************/
/*                                                                            */
/*                         C H A N G E  H I S T O R Y                         */
/*                                                                            */
/******************************************************************************/

// Date		Version	Description
//------------------------------------------------------------------------
// 081101		First revision, adapted from existing "jp" 
//                      debug proxy.                               jb, rmd
// 090608               A few hacks for VPI compatibilty added          jb

#ifndef GDB_H
#define GDB_H

#include <sys/types.h>
#include <inttypes.h>

extern void HandleServerSocket(void);
extern void handle_rsp (void);
int GetServerSocket(const char* name, const char* proto, int port);
extern void JTAGRequest(void);
void setup_or32(void);
void gdb_close();
void rsp_set_server_port(int);

//extern int err;

/* All JTAG chains.  */
enum jtag_chains
  {
    SC_GLOBAL,      /* 0 Global BS Chain */
    SC_RISC_DEBUG,  /* 1 RISC Debug Interface chain */
    SC_RISC_TEST,   /* 2 RISC Test Chain */
    SC_TRACE,       /* 3 Trace Chain */
    SC_REGISTER,    /* 4 Register Chain */
    SC_WISHBONE,    /* 5 Memory chain */
    SC_BLOCK,       /* 6 Block Chains */
  };

/* See JTAG documentation about these.  */
#define JI_SIZE (4)
enum jtag_instr
  {
    JI_EXTEST,
    JI_SAMPLE_PRELOAD,
    JI_IDCODE,
    JI_CHAIN_SELECT,
    JI_INTEST,
    JI_CLAMP,
    JI_CLAMPZ,
    JI_HIGHZ,
    JI_DEBUG,
    JI_BYPASS = 0xF
  };

/* JTAG registers.  */
#define JTAG_MODER  (0x0)
#define JTAG_TSEL   (0x1)
#define JTAG_QSEL   (0x2)
#define JTAG_SSEL   (0x3)
#define JTAG_RISCOP (0x4)
#define JTAG_RECWP0 (0x10)
#define JTAG_RECBP0 (0x1b)

/* This is repeated from gdb tm-or1k.h There needs to be
   a better mechanism for tracking this, but I don't see
   an easy way to share files between modules. */

typedef enum {
  JTAG_COMMAND_READ = 1,
  JTAG_COMMAND_WRITE = 2,
  JTAG_COMMAND_BLOCK_READ = 3,
  JTAG_COMMAND_BLOCK_WRITE = 4,
  JTAG_COMMAND_CHAIN = 5,
} JTAG_proxy_protocol_commands;

/* Each transmit structure must begin with an integer
   which specifies the type of command. Information
   after this is variable. Make sure to have all information
   aligned properly. If we stick with 32 bit integers, it
   should be portable onto every platform. These structures
   will be transmitted across the network in network byte
   order.
*/

/* Special purpose groups */

#define OR1K_SPG_SIZE_BITS  11
#define OR1K_SPG_SIZE       (1 << OR1K_SPG_SIZE_BITS)

#define OR1K_SPG_SYS      0
#define OR1K_SPG_DMMU     1
#define OR1K_SPG_IMMU     2
#define OR1K_SPG_DC       3
#define OR1K_SPG_IC       4
#define OR1K_SPG_MAC      5
#define OR1K_SPG_DEBUG    6
#define OR1K_SPG_PC       7
#define OR1K_SPG_PM       8
#define OR1K_SPG_PIC      9
#define OR1K_SPG_TT      10
#define OR1K_SPG_FPU     11


typedef struct {
  uint32_t command;
  uint32_t length;
  uint32_t address;
  uint32_t data_H;
  uint32_t data_L;
} JTAGProxyWriteMessage;

typedef struct {
  uint32_t command;
  uint32_t length;
  uint32_t address;
} JTAGProxyReadMessage;

typedef struct {
  uint32_t command;
  uint32_t length;
  uint32_t address;
  int32_t  nRegisters;
  uint32_t data[1];
} JTAGProxyBlockWriteMessage;

typedef struct {
  uint32_t command;
  uint32_t length;
  uint32_t address;
  int32_t  nRegisters;
} JTAGProxyBlockReadMessage;

typedef struct {
  uint32_t command;
  uint32_t length;
  uint32_t chain;
} JTAGProxyChainMessage;

/* The responses are messages specific, however convention
   states the first word should be an error code. Again,
   sticking with 32 bit integers should provide maximum
   portability. */

typedef struct {
  int32_t status;
} JTAGProxyWriteResponse;

typedef struct {
  int32_t status;
  uint32_t data_H;
  uint32_t data_L;
} JTAGProxyReadResponse;
  
typedef struct {
  int32_t status;
} JTAGProxyBlockWriteResponse;

typedef struct {
  int32_t status;
  int32_t nRegisters;
  uint32_t data[1];
  /* uint32_t data[nRegisters-1] still unread */
} JTAGProxyBlockReadResponse;

typedef struct {
  int32_t status;
} JTAGProxyChainResponse;


#endif /* GDB_H */
