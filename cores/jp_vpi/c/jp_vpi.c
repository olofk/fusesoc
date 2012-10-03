/*$$HEADER*/
/******************************************************************************/
/*                                                                            */
/*                    H E A D E R   I N F O R M A T I O N                     */
/*                                                                            */
/******************************************************************************/

// Project Name                   : ORPSoCv2
// File Name                      : jp_vpi.c
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

/*$$DESCRIPTION*/
/******************************************************************************/
/*                                                                            */
/*                           D E S C R I P T I O N                            */
/*                                                                            */
/******************************************************************************/
//
// Implements communication between verilog simulator and RSP server
//
//
/*
Functions used via the Verilog Procedural Interface (VPI), in a verilog
simulation of an OpenRISC processor, providing a means of communication to the
simulatin for a GDB stub.

The communication between the GDB stub and this module is via a "custom"
protocol, which is decoded into the verilog debug task module and the
appropriate transactions are performed with the debug interface inside the
OpenRISC design.
    
Operation:
See the verilog file containing the calls to the VPI tasks  we outline in this
file for exact details of how they are  used (debug_vpi_module.v), but
following is a brief outline of how it is meant to work.

The RSP GDB stub is initialised after compile via a VPI callback
(cbEndOfCompile). A process is forked off to run the RSP server, and IPC is via
pipes. Note: This is probably an extremely ineffecient way to do this as the
fork() creates a copy of the program, including it's ~200MB memory space, so
maybe a different method should be worked out for massive sims, but for smaller
OpenRISC designs on a power machine this is not a problem.

The verilog debug module polls for incoming commands from the GDB stub at a
#delay rate set in the verilog code.

The port which the GDB server runs on is #define'd in this file by
RSP_SERVER_PORT.

When a GDB connection is established, the state of the processor is downloaded
by GDB, so expect a slight delay after connection.

To close down the simulation gracefully, issue a "detach" command from GDB.
This will close the connection with the stub and will also send a message to
$finish the simulation.

Note: Simulation reset is untested, but should probably work OK.

Note: Reading uninitialised memory which returns Xs will break things.
Specifically, the CRC generation breaks, and then many other things. So to help
avoid hours of X tracing, ensure you're reading initialised space from GDB.

To Do: 
* Comment this better! Sorry, it's a little lacking in this area.
* Block transfers (ie. what happens when "load"ing from GDB) ignore any bytes
  over the word boundary at the end of a transfer. Currently a warning printf
  will appear.
* Make the RSP server process not be a complete copy of the vvp image - ie.
  don't fork() in the sim, maybe compile and exec() a separate app for this.

*/


/* EXAMPLE
// Associate C Function with a New System Task
voi
d registerHelloSystfs() {
  s_vpi_systf_data task_data_s;
  p_vpi_systf_data task_data_p = &task_data_s;
  task_data_p->type = vpiSysTask;
  task_data_p->tfname = "$hello";
  task_data_p->calltf = hello;
  task_data_p->compiletf = 0;
  
  vpi_register_systf(task_data_p);
}

*/


/*
To associate your C function with a system task, create a 
data structure of type s_vpi_systf_data and a pointer to 
that structure. The vpi_systf_data data type is defined in 
the vpi_user.h include file. Below is the data structure 
of s_vpi_systf_data.

 typedef struct t_vpi_systf_data {
   PLI_INT32 type;     // vpiSysTask, vpiSysFunc - task not return val, Func does
   PLI_INT32 sysfunctype; // vpiSysTask, vpi[Int,Real,Time,Sized, SizedSigned]Func - if it's a func, this is the typ of return 
   PLI_BYTE8 *tfname;  // First character must be `$' 
   PLI_INT32 (*calltf)(PLI_BYTE8 *); //pointer to the function
   PLI_INT32 (*compiletf)(PLI_BYTE8 *); // pointer to a function that the simulator calls 
                                        // when it's compiled - can be NULL
   PLI_INT32 (*sizetf)(PLI_BYTE8 *); // For sized function callbacks only, This field is a 
                                     // pointer to a routine that returns the size, in bits, 
                                     // of the value that the system task or function returns.
   PLI_BYTE8 *user_data; --optional extra data?
 } s_vpi_systf_data, *p_vpi_systf_data;
*/



/*$$CHANGE HISTORY*/
/******************************************************************************/
/*                                                                            */
/*                         C H A N G E  H I S T O R Y                         */
/*                                                                            */
/******************************************************************************/
// Date		Version	Description
//------------------------------------------------------------------------
// 090501		Imported code from "jp" VPI project     	jb
//                      Changed to use pipes instead of sockets         jb




#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/select.h>
#include <sys/poll.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <ctype.h>
#include <string.h>
#include <stdarg.h>
#include <stdint.h>
#include <signal.h>
#include <inttypes.h>

// VPI includes
#include <vpi_user.h>

#ifdef CDS_VPI
// Cadence ncverilog specific include
#include <vpi_user_cds.h>
#endif

// Includes for the RSP server side of things
#include "gdb.h"
#include "rsp-rtl_sim.h"
#include "rsp-vpi.h"

// Define the port we open the RSP server on
#define RSP_SERVER_PORT 50002

//Function to register the function which sets up the sockets interface
void register_init_rsp_server_functions() ;
// Function which sets up the socket interface
void init_rsp_server();
//install a callback on simulation reset which calls setup
void setup_reset_callbacks();
//install a callback on simulation compilation finish
void setup_endofcompile_callbacks();
//install a callback on simulation finish
void setup_finish_callbacks();
//callback function which closes and clears the socket file descriptors
// on simulation reset
void sim_reset_callback();
void sim_endofcompile_callback();
void sim_finish_callback();

void register_check_for_command();
void register_get_command_address();
void register_get_command_data();
void register_return_command_block_data();
void register_return_command_data();
void register_get_command_block_data();
void register_return_response();

void check_for_command();
void get_command_address();
void get_command_data();
void get_command_block_data();
void return_command_data();
void return_command_block_data();
void return_response();

  
#include <time.h>

uint32_t vpi_to_rsp_pipe[2]; // [0] - read, [1] - write
uint32_t rsp_to_vpi_pipe[2]; // [0] - read, [1] - write
uint32_t command_pipe[2]; // RSP end writes, VPI end reads ONLY

/* Global static to store the child rsp server PID if we want to kill it */
static pid_t rsp_server_child_pid = (pid_t) 0; // pid_t is just a signed int


/********************************************************************/
/* init_rsp_server
 * 
 * Fork off the rsp server process
 *                                                                   /
/********************************************************************/
void init_rsp_server(){


  // First get the port number to start the RSP server on
  
  vpiHandle systfref, args_iter, argh;
  
  struct t_vpi_value argval;

  int value,i;

  int n;

  int portNum;
  
  char* send_buf;

  /*

  // Currently removed - ability to call $rsp_init_server() with a 
  // port number as parameter. Hardcoded allows us to run this as
  // a callback after compiile (cbEndOfCompile)

  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 

  // get a handle on the object passed to the function
  argh = vpi_scan(args_iter);

  // now store the command value back in the sim
  argval.format = vpiIntVal;
  
  // Now set the data value
  vpi_get_value(argh, &argval);

  portNum = (int) argval.value.integer;
  
  // Cleanup and return
  vpi_free_object(args_iter);
  
  // We should now have our port number.

  */

  // Fork. Let the child run the RSP server
  pid_t pid;
  int rv;

  if(DBG_JP_VPI) printf("jp_vpi: init_rsp_server\n");

  // Setup pipes
  if(pipe(vpi_to_rsp_pipe) == -1)
    {
      perror("jp_vpi: init_rsp_server pipes");
      exit(1);
    }
  if(pipe(rsp_to_vpi_pipe) == -1)
    {
      perror("jp_vpi: init_rsp_server pipes");
      exit(1);
    }
  if(pipe(command_pipe) == -1)
    {
      perror("jp_vpi: init_rsp_server pipes");
      exit(1);
    }

  // Set command pipe to be non-blocking
#if defined (STRIDE) || (defined (pfa) && defined (HAVE_PTYS)) || defined (AIX)
  {
    int one = 1;
    ioctl (command_pipe[0], FIONBIO, &one);
  }
#endif
  
#ifdef O_NONBLOCK /* The POSIX way */
  fcntl (command_pipe[0], F_SETFL, O_NONBLOCK);
#elif defined (O_NDELAY)
  fcntl (command_pipe[0], F_SETFL, O_NDELAY);
#endif /* O_NONBLOCK */
  
  // Check on the child process. If it has not been started it will
  // be 0, else it will be something else and we'll just return
  if ((int) rsp_server_child_pid > 0)
    return;

  switch(pid=fork())
    {
    case -1:
      perror("fork");
      exit(1);
      break;
    case 0: // Child
      run_rsp_server(RSP_SERVER_PORT);
      // exit if it ever returns, which it shouldn't
      exit(0);
      break;
    default:
      //  We're the parent process, so continue on.
      rsp_server_child_pid = pid;
      break;
    }

  // Parent will only ever get this far...

  return;
  
}

void register_init_rsp_server_functions() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$init_rsp_server", 
			   (void *)init_rsp_server, 
			   0, 
			   0, 
			   0};
  
  vpi_register_systf(&data);
  
  return;
}

void print_command_string(unsigned char cmd)
{
  switch(cmd)
    {
    case 0x1 :
      printf("  TAP instruction register set\n");
      break;
    case 0x2 :
      printf("  set debug chain\n");
      break;
    case 0x3 :
      printf("  CPU control (stall/reset) reg write\n");
      break;
    case 0x4 :
      printf("  CPU control (stall/reset) reg read\n");
      break;
    case 0x5 :
      printf("  CPU reg write\n");
      break;
    case 0x6 :
      printf("  CPU reg read\n");
      break;
    case 0x7 :
      printf("  WB write\n");
      break;
    case 0x8 :
      printf("  WB read 32\n");
      break;
    case 0x9 :
      printf("  WB block write 32\n");
      break;
    case 0xa :
      printf("  WB block read 32\n");
      break;
    case 0xb :
      printf("  reset\n");
      break;
    case 0xc :
      printf("  read jtag id\n");
      break;
    case 0xd :
      printf("  detach\n");
      break;
    case 0xe :
      printf("  WB read 8\n");
      break;
    }
}

// See if there's anything on the FIFO for us

void check_for_command(char *userdata){

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n;

  unsigned char data;

  //if(DBG_JP_VPI) printf("check_for_command\n");
  
  //n = read(rsp_to_vpi_pipe[0], &data, 1);
  
  n = read(command_pipe[0], &data, 1);

  if ( ((n < 0) && (errno == EAGAIN)) || (n==0) )
    {
      // Nothing in the fifo this time, let's return
      return;
    }
  else if (n < 0)
    {
      // some sort of error
      perror("check_for_command");

      exit(1);
    }
  
  if (DBG_JP_VPI)
  {
    printf("jp_vpi: c = %x:",data);
    print_command_string(data);
    fflush(stdout);
  }
  
  // Return the command to the sim
  
  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 

  // get a handle on the variable passed to the function
  argh = vpi_scan(args_iter);

  // now store the command value back in the sim
  argval.format = vpiIntVal;
  
  // Now set the command value
  vpi_get_value(argh, &argval);

  argval.value.integer = (uint32_t) data;

  // And vpi_put_value() it back into the sim
  vpi_put_value(argh, &argval, NULL, vpiNoDelay);
  
  // Cleanup and return
  vpi_free_object(args_iter);

  n = write(vpi_to_rsp_pipe[1],&data,1);
  if (DBG_JP_VPI) printf("jp_vpi: r");

  if (DBG_JP_VPI) printf("\n");
   
  return;
}

void get_command_address(char *userdata){

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n;

  uint32_t data;
  
  char* recv_buf;

  recv_buf = (char *) &data; // cast data as our receive char buffer

  n = read(rsp_to_vpi_pipe[0],recv_buf,4);
  if (n<0)
    {
      //client has closed connection
      //attempt to close and return gracefully
      return;
    }      
  
  if (DBG_JP_VPI) printf("jp_vpi: get_command_address adr=0x%.8x\n",data);

  // now put the address into the argument passed to the task
  
  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 

  // get a handle on the variable passed to the function
  argh = vpi_scan(args_iter);

  // now store the command value back in the sim
  argval.format = vpiIntVal;
  
  // Now set the address value
  vpi_get_value(argh, &argval);
  argval.value.integer = (uint32_t) data;
  
  // And vpi_put_value() it back into the sim
  vpi_put_value(argh, &argval, NULL, vpiNoDelay);
  
  // Cleanup and return
  vpi_free_object(args_iter);
   
   return;

}

void get_command_data(char *userdata){

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n = 0;

  uint32_t data;
  
  char* recv_buf;

  recv_buf = (char *) &data; // cast data as our receive char buffer

 read_command_data_again:  
  n = read(rsp_to_vpi_pipe[0],recv_buf,4);
  
  if ((n < 4) && errno==EAGAIN)
    goto read_command_data_again;
  else if (n < 4)
    {
      printf("jp_vpi: get_command_data errno: %d\n",errno);
      perror("jp_vpi: get_command_data read failed");
    }
  if (DBG_JP_VPI) printf("jp_vpi: get_command_data = 0x%.8x\n",data);

  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 

  // get a handle on the variable passed to the function
  argh = vpi_scan(args_iter);

  // now store the command value back in the sim
  argval.format = vpiIntVal;
  
  // Now set the data value
  vpi_get_value(argh, &argval);
  argval.value.integer = (uint32_t) data;
  
  // And vpi_put_value() it back into the sim
  vpi_put_value(argh, &argval, NULL, vpiNoDelay);
  
  // Cleanup and return
  vpi_free_object(args_iter);
   
   return;

}


void get_command_block_data(){ // $get_command_block_data(length, mem_array)

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n;

  uint32_t data;
  uint32_t length;

  char* recv_buf;

  // Now setup the handles to verilog objects and check things
  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 
  
  // get a handle on the length variable
  argh = vpi_scan(args_iter);
  
  argval.format = vpiIntVal;
  
  // get the value for the length object
  vpi_get_value(argh, &argval);

  // now set length
  length = argval.value.integer;

  int num_words = length/4;
  
  //if((length % 4) != 0) vpi_printf("length of %d bytes is not exactly word-aligned\n",length);
  // If non-word aligned we throw away remainder
  int throw_away_bytes = length %4;

  int loaded_words = 0;

  if(DBG_JP_VPI)printf("jp_vpi: get_command_block_data: length=%d, num_words=%d\n",length,num_words);

  // now get a handle on the next object (memory array)
  argh = vpi_scan(args_iter);

  // check we got passed a memory (array of regs)
  if (!((vpi_get(vpiType, argh) == vpiMemory) 
#ifdef MODELSIM_VPI
	|| (vpi_get(vpiType, argh) == vpiRegArray)
#endif
	))
    { 
      vpi_printf("jp_vpi: ERROR: did not pass a memory to get_command_block_data\n");
      vpi_printf("jp_vpi: ERROR: was passed type %d\n", (int)vpi_get(vpiType, argh));
      return;
    }
  
  // check the memory we're writing into is big enough
  if (vpi_get(vpiSize, argh) < num_words ) 
    {
      vpi_printf("jp_vpi: ERROR: buffer passed to get_command_block_data too small. size is %d words, needs to be %d\n",
		 vpi_get(vpiSize, argh), num_words);
      return;
    } 
  
  vpiHandle array_word;

  // Loop to load the words
  while (loaded_words < num_words) {
    
    recv_buf = (char *) &data;
    
    // blocking receive for data block
    n = read(rsp_to_vpi_pipe[0],recv_buf,4);
    
    // now get a handle on the current word we want in the array that was passed to us
    array_word = vpi_handle_by_index(argh, loaded_words);
    
    if (array_word != NULL)
      {
	argval.value.integer = (uint32_t) data;
	
	// And vpi_put_value() it back into the sim
	vpi_put_value(array_word, &argval, NULL, vpiNoDelay);
      }
    else
      return;
    
    loaded_words++;
  }
  // TODO: This is a quick fix, should be delt with properly!!
  if (throw_away_bytes) 
    {
      //printf("reading off %d extra data bytes\n",throw_away_bytes);
      n = read(rsp_to_vpi_pipe[0],&data,throw_away_bytes);
      //printf("read off %d bytes \n",n);
    }
  
  // Cleanup and return
  vpi_free_object(args_iter);
  
  return;

}

void return_command_data(char *userdata){

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n, length;

  uint32_t data;
  
  char* send_buf;

  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 

  // get a handle on the length variable
  argh = vpi_scan(args_iter);
  
  argval.format = vpiIntVal;
  
  // get the value for the length object
  vpi_get_value(argh, &argval);

  // now set length
  length = argval.value.integer;

  // get a handle on the object passed to the function
  argh = vpi_scan(args_iter);

  // now store the command value back in the sim
  argval.format = vpiIntVal;
  
  // Now set the data value
  vpi_get_value(argh, &argval);

  data = (uint32_t) argval.value.integer;
  
  // Cleanup and return
  vpi_free_object(args_iter);

  if (DBG_JP_VPI) printf("jp_vpi: return_command_data %d bytes, 0x%.8x\n",length,data);
  
  send_buf = (char *) &data; //cast our long as a char buf
  
  // write the data back
  n = write(vpi_to_rsp_pipe[1],send_buf,length);

  return;

}

void return_command_block_data(){

  vpiHandle systfref, args_iter, argh;

  struct t_vpi_value argval;

  int value,i;

  int n;

  uint32_t data;
  uint32_t length;

  char *block_data_buf;
  uint32_t *block_word_data_buf_ptr;

  int num_words;
  int sent_words = 0;

  vpiHandle array_word;
  
  // Now setup the handles to verilog objects and check things
  // Obtain a handle to the argument list
  systfref = vpi_handle(vpiSysTfCall, NULL);
  
  // Now call iterate with the vpiArgument parameter
  args_iter = vpi_iterate(vpiArgument, systfref); 
  
  // get a handle on the length variable
  argh = vpi_scan(args_iter);
  
  argval.format = vpiIntVal;
  
  // get the value for the length object
  vpi_get_value(argh, &argval);

  // now set length
  length = argval.value.integer;

  // now get a handle on the next object (memory array)
  argh = vpi_scan(args_iter);

  // check we got passed a memory (array of regs) (modelsim passes back a vpiRegArray, so check for that too)
  if (!((vpi_get(vpiType, argh) == vpiMemory) 
#ifdef MODELSIM_VPI
	|| (vpi_get(vpiType, argh) == vpiRegArray)
#endif
      ))
    { 
      vpi_printf("jp_vpi: ERROR: did not pass a memory to return_command_block_data\n");
      vpi_printf("jp_vpi: ERROR: was passed type %d\n", (int)vpi_get(vpiType, argh));
      return;
    }
  
  // We have to alloc memory here for lengths > 4
  if (length > 4);
  {
    block_data_buf = (char*) malloc(length * sizeof(char));
    if (block_data_buf == NULL)
      {
	vpi_printf("jp_vpi: return_command_block_data: Error. Could not allocate memory\n");
	// Cleanup and return
	vpi_free_object(args_iter);
	return;
      }

    // Now cast it as a uint32_t array
    block_word_data_buf_ptr = (uint32_t *) block_data_buf;
  }

  num_words = length / 4; // We're always going to be dealing with whole words here
  
  if (DBG_JP_VPI) printf("jp_vpi: return_command_block_data: num_words %d\n",
			 num_words);

    // Loop to load the words
  while (sent_words < num_words) {
    
    // Get a handle on the current word we want in the array that was passed to us
    array_word = vpi_handle_by_index(argh, sent_words);
    
    if (array_word != NULL)
      {
	vpi_get_value(array_word, &argval);
	
	data = (uint32_t) argval.value.integer;
	
	block_word_data_buf_ptr[sent_words] = data;
      }
    else
      return;

    if (DBG_JP_VPI) printf ( "jp_vpi: return_command_block_data: word %d 0x%.8x\n",
			     sent_words, data);
    sent_words++;
  }
  
  if (!(length > 4))
    {
      block_data_buf = (char *) &data; 
    }
  
  n = write(vpi_to_rsp_pipe[1],block_data_buf,length);

  
  if (length > 4)
    {
      // Free the array
      free(block_data_buf);
    }
    
  
  // Cleanup and return
  vpi_free_object(args_iter);

  return;

}



void return_response(char *userdata){

  int n;
  
  char resp = 0;
  
  // send a response byte
  n = write(vpi_to_rsp_pipe[1],&resp,1);
  
  if (DBG_JP_VPI) printf("jp_vpi: ret\n\n");
  
  return;

}

void register_check_for_command() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$check_for_command", 
			   (void *)check_for_command, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}

void register_get_command_address() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$get_command_address", 
			   (void *)get_command_address, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}

void register_get_command_data() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$get_command_data", 
			   (void *)get_command_data, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}

void register_get_command_block_data() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$get_command_block_data", 
			   (void *)get_command_block_data, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}


void register_return_command_block_data() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$return_command_block_data", 
			   (void *)return_command_block_data, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}

void register_return_command_data() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$return_command_data", 
			   (void *)return_command_data, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}

void register_return_response() {
  s_vpi_systf_data data = {vpiSysTask, 
			   0, 
			   "$return_response", 
			   (void *)return_response, 
			   0, 
			   0, 
			   0};

  vpi_register_systf(&data);

  return;
}


void setup_reset_callbacks()
{
  
  // here we setup and install callbacks for 
  // the setup and management of connections to
  // the simulator upon simulation start and 
  // reset

  static s_vpi_time time_s = {vpiScaledRealTime}; 
  static s_vpi_value value_s = {vpiBinStrVal}; 
  static s_cb_data cb_data_s =  
    {
      cbEndOfReset, // or start of simulation - initing socket fds etc
      (void *)sim_reset_callback,
      NULL,
      &time_s,
      &value_s
    }; 
  
  cb_data_s.obj = NULL;  /* trigger object */ 

  cb_data_s.user_data = NULL;

  // actual call to register the callback
  vpi_register_cb(&cb_data_s);  

}

void sim_reset_callback()
{

  // nothing to do!

  return;

}

void setup_endofcompile_callbacks()
{
  
  // here we setup and install callbacks for 
  // simulation finish

  static s_vpi_time time_s = {vpiScaledRealTime}; 
  static s_vpi_value value_s = {vpiBinStrVal}; 
  static s_cb_data cb_data_s =  
    {
      cbEndOfCompile, // end of compile
      (void *)sim_endofcompile_callback,
      NULL,
      &time_s,
      &value_s
    }; 
  
  cb_data_s.obj = NULL;  /* trigger object */ 

  cb_data_s.user_data = NULL;

  // actual call to register the callback
  vpi_register_cb(&cb_data_s);  

}

void sim_endofcompile_callback()
{
  // Init the RSP server
  init_rsp_server(); // Start the RSP server from here!

}


void setup_finish_callbacks()
{
  
  // here we setup and install callbacks for 
  // simulation finish

  static s_vpi_time time_s = {vpiScaledRealTime}; 
  static s_vpi_value value_s = {vpiBinStrVal}; 
  static s_cb_data cb_data_s =  
    {
      cbEndOfSimulation, // end of simulation
      (void *)sim_finish_callback,
      NULL,
      &time_s,
      &value_s
    }; 
  
  cb_data_s.obj = NULL;  /* trigger object */ 

  cb_data_s.user_data = NULL;

  // actual call to register the callback
  vpi_register_cb(&cb_data_s);  

}

void sim_finish_callback()
{
  printf("Closing RSP server\n");
  // Close down the child process, if it hasn't already
  kill(rsp_server_child_pid,SIGTERM);
}



// Register the new system task here
void (*vlog_startup_routines[ ] ) () = {
  register_init_rsp_server_functions,
#ifdef CDS_VPI
  // this installs a callback on simulator reset - something which 
  // icarus does not do, so we only do it for cadence currently
  setup_reset_callbacks, 
#endif
  setup_endofcompile_callbacks,
  setup_finish_callbacks,
  register_check_for_command,
  register_get_command_address,
  register_get_command_data,
  register_get_command_block_data,
  register_return_command_data,
  register_return_command_block_data,
  register_return_response,
  0  // last entry must be 0 
}; 



// Entry point for testing development of the vpi functions
int main(int argc, char *argv[])
{

  return 0;
  
}



