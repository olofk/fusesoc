/*$$HEADER*/
/******************************************************************************/
/*                                                                            */
/*                    H E A D E R   I N F O R M A T I O N                     */
/*                                                                            */
/******************************************************************************/

// Project Name                   : ORPSoCv2
// File Name                      : rsp-rtl_sim.c
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


/* Establishes GDB proxy server and communicates via pipes
   to some functions running under the VPI in an RTL sim */

#include <stdio.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <assert.h>

#include <ctype.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdarg.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>

#include "gdb.h"
#include "rsp-rtl_sim.h"
#include "rsp-vpi.h"

static int err = 0;

/* Currently selected scan chain - just to prevent unnecessary
   transfers. */
static int current_chain = -1;

/* The chain that should be currently selected. */
static int dbg_chain = -1;

/* Crc of current read or written data.  */
static int crc_r, crc_w = 0;

/* Generates new crc, sending in new bit input_bit */
static uint32_t crc_calc(uint32_t crc, int input_bit) {
  uint32_t d = (input_bit&1) ? 0xfffffff : 0x0000000;
  uint32_t crc_32 = ((crc >> 31)&1) ? 0xfffffff : 0x0000000;
  crc <<= 1;
  return crc ^ (d ^ crc_32) & DBG_CRC_POLY;
}

/* VPI communication prototyopes */
static void get_response_from_vpi();
static void get_word_from_vpi();
static void get_byte_from_vpi();
static void get_block_data_from_vpi(int len, uint32_t *data);
static void send_data_to_vpi(uint32_t data);
static void send_block_data_to_vpi(int len, uint32_t *data);
static void send_address_to_vpi(uint32_t address);
static void send_command_to_vpi(char CMD);

void send_command_to_vpi(char CMD)
{
  // first thing we do  is send a command
  // and wait for an ack
  int n;
  char cmd_resp;
  
  if (DBG_CALLS)printf("send_command_to_vpi: cmd 0x%x \n", CMD);
  
  //n = write(rsp_to_vpi_pipe[1],&CMD, 1); // send the command to the sim
  n = write(command_pipe[1],&CMD, 1); // send the command to the sim
  
  if (n < 0)   error("ERROR writing to VPI FIFO");
  
  n = read(vpi_to_rsp_pipe[0],&cmd_resp,1); // block and wait for the ack
  
  if (cmd_resp != CMD) error("Response from RTL sim incorrect"); //check it acked with cmd

  return;
}

void send_address_to_vpi(uint32_t address)
{
  // Now send address
  int n;

  char* send_buf;

  if (DBG_CALLS)printf("send_address_to_vpi: address 0x%.8x\n",address);

  send_buf = (char *) &address;
  
  n = write(rsp_to_vpi_pipe[1],send_buf, 4); // send the address to the sim
  
  if (n < 0)   error("ERROR writing to VPI socket");
  
  return;
}

void send_data_to_vpi(uint32_t data)
{
  // Now send data
  int n;

  char* send_buf;

  if (DBG_CALLS)printf("send_data_to_vpi: data 0x%.8x\n",data);

  send_buf = (char *) &data;
  
  n = write(rsp_to_vpi_pipe[1],send_buf, 4); // Write the data to the socket
  
  if (n < 0)   error("ERROR writing to VPI socket");
  
  return;
  
}

void send_block_data_to_vpi(int len, uint32_t *data)
{
  // Now send data
  int n, i;
  
  char* send_buf;

  if (DBG_CALLS)printf("send_block_data_to_vpi: len %d\n",len);
  
  send_buf = (char *) data;
  
  n = write(rsp_to_vpi_pipe[1],send_buf, len); // Write the data to the fifo
  
  if (n < 0)   error("ERROR writing to VPI socket");
  
  return;
  
}


void get_byte_from_vpi(uint8_t* data)
{
  
  int n;
  
  uint8_t inc_data;
  
  char* recv_buf;
  
  recv_buf = (char*) &inc_data;
  
  n = read(vpi_to_rsp_pipe[0],recv_buf,1); // block and wait for the data

  if (DBG_VPI) printf("rsp-rtl_sim: get_byte_from_vpi: 0x%.8x\n",inc_data);

  *data = inc_data;
  
  return;

}

void get_word_from_vpi(uint32_t* data)
{
  
  int n;
  
  uint32_t inc_data;
  
  char* recv_buf;
  
  recv_buf = (char*) &inc_data;
  
  n = read(vpi_to_rsp_pipe[0],recv_buf,4); // block and wait for the data

  if (DBG_VPI) printf("rsp-rtl_sim: get_word_from_vpi: 0x%.8x\n",inc_data);

  *data = inc_data;
  
  return;

}

void get_block_data_from_vpi(int len, uint32_t* data)
{
  int n, i, status;
  
  uint32_t inc_data;
  
  char* recv_buf;

  uint32_t* data_ptr;
  
  recv_buf = (char *) data;

  n=0;

  if (DBG_CALLS)printf("rsp_rtl_sim: get_block_data_from_vpi len %d\n",len);
  
  while (n < len)
    {
      
      status = read(vpi_to_rsp_pipe[0], recv_buf, len - n); // block and wait for the data
      
      if (status > 0) n += status; // we read "status" number of bytes
      
    }
  
  
  if (DBG_VPI){
    printf("rsp-rtl_sim: get_block_data_from_vpi: %d bytes: ",len);
    for (i = 0;i < (len); i++)
      {
	if ((i%12) == 0) printf("\n\t");
	printf("%.2x",recv_buf[i]);
	if ((i%3) == 0) printf(" ");
	
      }
    printf("\n");
  }
  
  return;

}

void get_response_from_vpi()
{
  // Basically just wait for the response from VPI
  // by blocking wait on recv
  
  int n = 0;
  char tmp;

  if (DBG_CALLS)printf("get_response_from_vpi..");

  n = read(vpi_to_rsp_pipe[0],&tmp,1); // block and wait

  if (DBG_CALLS)printf("OK\n");
  
  return;
}

static void jp2_reset_JTAG() {
  int i;

  debug2("\nreset(");

  send_command_to_vpi(CMD_RESET);

  get_response_from_vpi();
  
  debug2(")\n");

}

/* Resets JTAG, and sets DEBUG scan chain */
 int dbg_reset() {
   
   int err;
   uint32_t id;
   
   jp2_reset_JTAG();

  /* set idcode jtag chain */
  send_command_to_vpi(CMD_JTAG_SET_IR);

  send_data_to_vpi(JI_IDCODE);

  get_response_from_vpi();

  /* now read out the jtag id */
  send_command_to_vpi(CMD_READ_JTAG_ID);
  
  //id = get_word_from_vpi();  
  get_word_from_vpi((uint32_t *)&id);  
  
  get_response_from_vpi();
 
  printf("JTAG ID = %08x\n", id);

  /* now set the chain to debug */
  send_command_to_vpi(CMD_JTAG_SET_IR);
  
  send_data_to_vpi(JI_DEBUG);
  
  get_response_from_vpi();

  current_chain = -1;
  return DBG_ERR_OK;
}

/* counts retries and returns zero if we should abort */
/* TODO: dinamically adjust timings for jp2 */
static int retry_no = 0;
int retry_do() {
  int i, err;
  printf("RETRY\n");
  //exit(2);
  if (retry_no >= NUM_SOFT_RETRIES) {
    if ((err = dbg_reset())) return err;
  } 
  if (retry_no >= NUM_SOFT_RETRIES + NUM_HARD_RETRIES) {
    retry_no = 0;
    return 0;
  }
  retry_no++;
  return 1;
}

/* resets retry counter */
void retry_ok() {
  retry_no = 0;
}

/* Sets scan chain.  */
int dbg_set_chain(int chain) {

  debug("\n");
  debug2("dbg_set_chain %d\n", chain);
  
  if (current_chain == chain)
    return DBG_ERR_OK;

  if (DBG_CALLS)printf("dbg_set_chain chain %d \n", chain);
  
  dbg_chain = chain;
  
  send_command_to_vpi(CMD_SET_DEBUG_CHAIN);
  
  send_data_to_vpi(chain);
  
  get_response_from_vpi();
  
  current_chain = chain;
  
  return DBG_ERR_OK;
}

/* writes a ctrl reg */
int dbg_ctrl(int reset, int stall) 
{
  
  debug("\n");
  debug2("ctrl\n");

  if (DBG_CALLS)printf("dbg_ctrl: reset %d stall %d \n", reset, stall);
  
  dbg_set_chain(dbg_chain);
  
  send_command_to_vpi(CMD_CPU_CTRL_WR);
  
  //send_data_to_vpi(((reset & 0x1) | ((stall&0x1)<<1)));
  send_data_to_vpi(((stall & 0x1) | ((reset&0x1)<<1)));
  
  get_response_from_vpi();

  return DBG_ERR_OK;
}

/* reads control register */
int dbg_ctrl_read(int *reset, int *stall) 
{
  
  uint32_t resp;
  
  dbg_set_chain(dbg_chain);
    
  debug("\n");
  debug2("ctrl\n");

  if (DBG_CALLS)printf("dbg_ctrl_read\n");
  
  dbg_set_chain(dbg_chain);
  
  send_command_to_vpi(CMD_CPU_CTRL_RD);
  
  get_word_from_vpi((uint32_t *)&resp);
  
  if (DBG_VPI) printf("rsp-rtl_sim: dbg_ctrl_read: 0x%.8x\n",resp);

  get_response_from_vpi();
  
  *reset = (int)(resp & 0x00000001);

  *stall = (int)((resp >> 1) & 0x00000001);
  
  return DBG_ERR_OK;
}

/* read a word from wishbone */
int dbg_wb_read32(uint32_t adr, uint32_t *data) 
{
  if (DBG_CALLS)printf("dbg_wb_read32: adr 0x%.8x \n",adr);

  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_RD32);
  
  send_address_to_vpi(adr);
  
  get_word_from_vpi(data);
  
  get_response_from_vpi();
  
  return 0;
}

/* read a word from wishbone */
int dbg_wb_read8(uint32_t adr, uint8_t *data) 
{
  if (DBG_CALLS)printf("dbg_wb_read8: adr 0x%.8x \n",adr);

  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_RD8);
  
  send_address_to_vpi(adr);
  
  get_byte_from_vpi(data);
  
  get_response_from_vpi();
  
  return 0;
}

/* write a word to wishbone */
int dbg_wb_write32(uint32_t adr, uint32_t data) 
{
  
  if (DBG_CALLS)printf("dbg_wb_write32: adr 0x%.8x data 0x%.8x\n",adr, data);
  
  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_WR);
  
  send_address_to_vpi(adr);

  send_data_to_vpi(sizeof(data));

  send_data_to_vpi(data);
  
  get_response_from_vpi();
  
  return 0;
} 

/* write a hword to wishbone */
int dbg_wb_write16(uint32_t adr, uint16_t data) 
{

  if (DBG_CALLS)printf("dbg_wb_write16: adr 0x%.8x data 0x%.4x\n",adr, data);

  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_WR);
  
  send_address_to_vpi(adr);

  send_data_to_vpi(sizeof(data));

  send_data_to_vpi(data);
  
  get_response_from_vpi();
  
  return 0;
} 

/* write a word to wishbone */
int dbg_wb_write8(uint32_t adr, uint8_t data) 
{

  if (DBG_CALLS)printf("dbg_wb_write8: adr 0x%.8x data 0x%.2x\n",adr, data);

  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_WR);
  
  send_address_to_vpi(adr);

  send_data_to_vpi(sizeof(data));

  send_data_to_vpi(data);
  
  get_response_from_vpi();
  
  return 0;
} 


/* read a block from wishbone */
int dbg_wb_read_block32(uint32_t adr, uint32_t *data, int len) 
{
  
  // len is in B Y T E S ! !

  if (DBG_VPI) printf("xbrsp-rtl_sim: block read len: %d from addr: 0x%.8x\n",len, adr);

  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_BLOCK_RD32);

  send_data_to_vpi(adr);

  send_data_to_vpi(len);

  get_block_data_from_vpi(len, data);

  get_response_from_vpi();
      
  return DBG_ERR_OK;
}

/* write a block to wishbone */
int dbg_wb_write_block32(uint32_t adr, uint32_t *data, int len) 
{

  if (DBG_CALLS)printf("dbg_wb_block32: adr 0x%.8x len %d bytes\n",adr, len);
  
  dbg_set_chain(DC_WISHBONE);
  
  send_command_to_vpi(CMD_WB_BLOCK_WR32);

  send_data_to_vpi(adr);
  
  send_data_to_vpi(len);

  send_block_data_to_vpi(len, data);

  get_response_from_vpi();

  return DBG_ERR_OK;
}

/* read a register from cpu */
int dbg_cpu0_read(uint32_t adr, uint32_t *data, uint32_t length) 
{

  if (DBG_CALLS)printf("dbg_cpu0_read: adr 0x%.8x\n",adr);
  
  dbg_set_chain(DC_CPU0);
  
  send_command_to_vpi(CMD_CPU_RD_REG);
  
  send_address_to_vpi(adr);

  send_data_to_vpi(length); // Added 090901 --jb

  get_block_data_from_vpi(length, data); // changed 090901 --jb //get_word_from_vpi(data);
  
  get_response_from_vpi();
  
  return 0;

}

/* write a cpu register */
int dbg_cpu0_write(uint32_t adr, uint32_t *data, uint32_t length) 
{

  if (DBG_CALLS)printf("dbg_cpu0_write: adr 0x%.8x\n",adr);
  
  dbg_set_chain(DC_CPU0);
  
  send_command_to_vpi(CMD_CPU_WR_REG);
  
  send_address_to_vpi(adr);
  
  send_data_to_vpi(length); // Added 090901 -- jb

  send_block_data_to_vpi(length, data); // Added 090901 -- jb
  
  get_response_from_vpi();
  
  return 0;
}

/* read a register from cpu */
int dbg_cpu1_read(uint32_t adr, uint32_t *data) {
  /*
  int err;
  if ((err = dbg_set_chain(DC_CPU1))) return err;
  if ((err = dbg_command(0x6, adr, 4))) return err;
  if ((err = dbg_go((unsigned char*)data, 4, 1))) return err;
  *data = ntohl(*data);
  */
  return DBG_ERR_OK;
}

/* write a cpu register */
int dbg_cpu1_write(uint32_t adr, uint32_t data) {
  /*
  int err;
  data = ntohl(data);
  if ((err = dbg_set_chain(DC_CPU1))) return err;
  if ((err = dbg_command(0x2, adr, 4))) return err;
  if ((err = dbg_go((unsigned char*)&data, 4, 0))) return err;
  */
  return DBG_ERR_OK;
}

/* read a register from cpu module */
int dbg_cpu1_read_ctrl(uint32_t adr, unsigned char *data) {
  /*
    int err;
    int r, s;
    if ((err = dbg_set_chain(DC_CPU1))) return err;
    if ((err = dbg_ctrl_read(&r, &s))) return err;
    *data = (r << 1) | s;
    */
  return DBG_ERR_OK;
}

/* write a cpu module register */
int dbg_cpu0_write_ctrl(uint32_t adr, unsigned char data) {
  int err;
  if ((err = dbg_set_chain(DC_CPU0))) return err;
  if ((err = dbg_ctrl(data & 2, data &1))) return err;
  return DBG_ERR_OK;
}

/* read a register from cpu module */
int dbg_cpu0_read_ctrl(uint32_t adr, unsigned char *data) {
  int err;
  int r, s;
  if ((err = dbg_set_chain(DC_CPU0))) return err;
  if ((err = dbg_ctrl_read(&r, &s))) return err;
  *data = (r << 1) | s;
  return DBG_ERR_OK;
}

void dbg_test() {
  int i;
  uint32_t npc, ppc, r1, insn, result;
  unsigned char stalled;
  //	uint32_t stalled;
  unsigned char read_byte;

  printf("  Stall or1k\n");
  dbg_cpu0_write_ctrl(0, 0x01);      // stall or1k

  dbg_cpu0_read_ctrl(0, &stalled);
  if (!(stalled & 0x1)) {
    printf("\tor1k stall failed. read: 0x%x\n", stalled);   // check stall or1k
    //exit(1);
  }

  /* Read NPC,PPC and SR regs, they are consecutive in CPU, at adr. 16, 17 and 18 */
  uint32_t pcs_and_sr[3]; 
  debug2("  Reading npc, ppc\n");
  dbg_cpu0_read(16, (uint32_t *)pcs_and_sr, 3 * 4);
  
  debug2("  Reading r1\n");
  dbg_cpu0_read(0x401, &r1, 4);
  printf("  Read      npc = %.8x ppc = %.8x r1 = %.8x\n", 
	 pcs_and_sr[0], pcs_and_sr[2], r1);
    
}

// Catch the term/int signals, close gdb then close ourselves
void catch_sigint(int sig_num)
{
  gdb_close();
  exit(0);
}

void dbg_client_detached(void)
{
  // Send this message back to the sim
  send_command_to_vpi(CMD_GDB_DETACH);
}


// This function is called after the fork in the VPI function.

void run_rsp_server(int portNum)
{
  // Send commands to init and reset debug interface
  dbg_reset();
  // Stall and read NPC, PPC etc
  dbg_test();
  
  set_rsp_server_port(portNum);

  // Install SIGINT/SIGTERM handlers, to close down gracefully
  signal(SIGINT, catch_sigint);
  signal(SIGTERM, catch_sigint);

  if (DBG_ON) printf("rsp-rtl_sim: starting handle_rsp()\n");
  // Now, start the RSP server. This should not return
  handle_rsp ();
  
  // Exit gracefully if it returns (shouldn't though)
  exit(0);

}


