/*$$HEADER*/
/******************************************************************************/
/*                                                                            */
/*                    H E A D E R   I N F O R M A T I O N                     */
/*                                                                            */
/******************************************************************************/

// Project Name                   : ORPSoCv2
// File Name                      : rsp-rtl_sim.h
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

#ifndef _RSP_RTL_SIM_H_
#define _RSP_RTL_SIM_H_

#include <stdint.h> // For uint32_t types

#define DEBUG 0
#define DEBUG2 0
#define DBG_ON  0
#define DBG_JP_VPI 0
#define DBG_VPI 0
#define DBG_CALLS 0


#define Boolean int
#define false 0
#define true 1

#if DEBUG==1
#define debug printf
#else
#define debug
#endif

#if DEBUG2==1
#define debug2 printf
#else
#define debug2
#endif


extern uint32_t vpi_to_rsp_pipe[2]; // [0] - read, [1] - write
extern uint32_t rsp_to_vpi_pipe[2]; // [0] - read, [1] - write
extern uint32_t command_pipe[2]; // RSP end writes, VPI end reads ONLY

#if (DEBUG) || (DEBUG2)
#define flush_debug() fflush(stdout)
#else
#define flush_debug()
#endif

# define JTAG_WAIT() usleep(1000)
# define JTAG_RETRY_WAIT() usleep (1000)

/* Selects crc trailer size in bits. Currently supported: 8 */
#define CRC_SIZE (8)

/* Scan chain size in bits.  */
#define SC_SIZE (4)

/* function to kick off this server */
void run_rsp_server(int);

/* read a word from wishbone */
int dbg_wb_read32(uint32_t adr, uint32_t *data);
int dbg_wb_read8(uint32_t adr, uint8_t* data);

/* write a word to wishbone */
int dbg_wb_write32(uint32_t adr, uint32_t data);
int dbg_wb_write16(uint32_t adr, uint16_t data);
int dbg_wb_write8(uint32_t adr, uint8_t data);

/* read a block from wishbone */
int dbg_wb_read_block32(uint32_t adr, uint32_t *data, int len);

/* write a block to wishbone */
int dbg_wb_write_block32(uint32_t adr, uint32_t *data, int len);

/* read a register from cpu */
int dbg_cpu0_read(uint32_t adr, uint32_t *data, uint32_t length);

/* read a register from cpu module */
int dbg_cpu0_read_ctrl(uint32_t adr, unsigned char *data);

/* write a cpu register */
int dbg_cpu0_write(uint32_t adr, uint32_t *data, uint32_t length);

/* write a cpu module register */
int dbg_cpu0_write_ctrl(uint32_t adr, unsigned char data);

/* send a message to the sim that the debugging client has disconnected */
void dbg_client_detached(void);

#define DC_SIZE           4
#define DC_STATUS_SIZE    4

#define DC_WISHBONE       0
#define DC_CPU0           1
#define DC_CPU1           2

#define DI_GO          0
#define DI_READ_CMD    1
#define DI_WRITE_CMD   2
#define DI_READ_CTRL   3
#define DI_WRITE_CTRL  4

#define DBG_CRC_SIZE      32
#define DBG_CRC_POLY      0x04c11db7

#define DBG_ERR_OK        0
#define DBG_ERR_CRC       8

#define NUM_SOFT_RETRIES  3
#define NUM_HARD_RETRIES  3
#define NUM_ACCESS_RETRIES 10

/* Possible errors are listed here.  */
enum enum_errors  /* modified <chris@asics.ws> CZ 24/05/01 */
{
  /* Codes > 0 are for system errors */

  ERR_NONE = 0,
  ERR_CRC = -1,
  ERR_MEM = -2,
  JTAG_PROXY_INVALID_COMMAND = -3,
  JTAG_PROXY_SERVER_TERMINATED = -4,
  JTAG_PROXY_NO_CONNECTION = -5,
  JTAG_PROXY_PROTOCOL_ERROR = -6,
  JTAG_PROXY_COMMAND_NOT_IMPLEMENTED = -7,
  JTAG_PROXY_INVALID_CHAIN = -8,
  JTAG_PROXY_INVALID_ADDRESS = -9,
  JTAG_PROXY_ACCESS_EXCEPTION = -10, /* Write to ROM */
  JTAG_PROXY_INVALID_LENGTH = -11,
  JTAG_PROXY_OUT_OF_MEMORY = -12,
};

#endif

