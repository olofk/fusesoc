/*
 * VPI JTAG master for openOCD.
 * Based on Julius Baxter's work on jp_vpi.c
 *
 * Copyright (C) 2012 Franck JULLIEN, <elec4fun@gmail.com>
 *
 * See file CREDITS for list of people who contributed to this
 * project.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 */

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
#include <arpa/inet.h>

// VPI includes
#include <vpi_user.h>

// Includes for the RSP server side of things
//#include "gdb.h"
//#include "rsp-rtl_sim.h"
//#include "rsp-vpi.h"

#include <time.h>

// Define the port we open the RSP server on
#define RSP_SERVER_PORT 50020

#define	XFERT_MAX_SIZE		512

const char * cmd_to_string[] = {"CMD_RESET", "CMD_TMS_SEQ", "CMD_SCAN_CHAIN"};

struct vpi_cmd {
	int cmd;
	unsigned char buffer_out[XFERT_MAX_SIZE];
	unsigned char buffer_in[XFERT_MAX_SIZE];
	int length;
	int nb_bits;
};

int listenfd = 0;
int connfd = 0;

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
void register_send_result_to_server();

void check_for_command();
void send_result_to_server();

int init_jtag_server(int port)
{
	struct sockaddr_in serv_addr;
	int flags;

	printf("Listening on port %d\n", port);

	listenfd = socket(AF_INET, SOCK_STREAM, 0);
	memset(&serv_addr, '0', sizeof(serv_addr));

	serv_addr.sin_family = AF_INET;
	serv_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	serv_addr.sin_port = htons(port);

	bind(listenfd, (struct sockaddr*)&serv_addr, sizeof(serv_addr));

	listen(listenfd, 10);

	printf("Waiting for client connection...");
	connfd = accept(listenfd, (struct sockaddr*)NULL, NULL);
	printf("ok\n");

	flags = fcntl(listenfd, F_GETFL, 0);
	fcntl(listenfd, F_SETFL, flags | O_NONBLOCK);

	return 0;
}

// See if there's anything on the FIFO for us

void check_for_command(char *userdata)
{
	vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;
	struct vpi_cmd vpi;
	int nb;
	int loaded_words = 0;

	// Get the command from TCP server
	if(!connfd)
	  init_jtag_server(RSP_SERVER_PORT);
	nb = read(connfd, &vpi, sizeof(struct vpi_cmd));

	if (((nb < 0) && (errno == EAGAIN)) || (nb == 0)) {
		// Nothing in the fifo this time, let's return
		return;
	} else {
		if (nb < 0) {
			// some sort of error
			perror("check_for_command");
			exit(1);
		}
	}
/*
	printf("\nReceived command:\n");
	printf("cmd     = %s\n", cmd_to_string[vpi.cmd]);
	printf("length  = %d\n", vpi.length);
	if (vpi.length) {
		printf("nb_bits = %d\n", vpi.nb_bits);
		printf("buffer  = ");
		for (i = 0; i < vpi.length; i++)
			printf("%02X ", vpi.buffer_out[i]);
		printf("\n");
	}
*/
/************* vpi.cmd to VPI ******************************/

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

	argval.value.integer = (uint32_t)vpi.cmd;

	// And vpi_put_value() it back into the sim
	vpi_put_value(argh, &argval, NULL, vpiNoDelay);

/************* vpi.length to VPI ******************************/

	// now get a handle on the next object (memory array)
	argh = vpi_scan(args_iter);
	// now store the command value back in the sim
	argval.format = vpiIntVal;
	// Now set the command value
	vpi_get_value(argh, &argval);

	argval.value.integer = (uint32_t)vpi.length;

	// And vpi_put_value() it back into the sim
	vpi_put_value(argh, &argval, NULL, vpiNoDelay);

/************* vpi.nb_bits to VPI ******************************/

	// now get a handle on the next object (memory array)
	argh = vpi_scan(args_iter);
	// now store the command value back in the sim
	argval.format = vpiIntVal;
	// Now set the command value
	vpi_get_value(argh, &argval);

	argval.value.integer = (uint32_t)vpi.nb_bits;

	// And vpi_put_value() it back into the sim
	vpi_put_value(argh, &argval, NULL, vpiNoDelay);

/*****************vpi.buffer_out to VPI ********/

	// now get a handle on the next object (memory array)
	argh = vpi_scan(args_iter);
	vpiHandle array_word;

	// Loop to load the words
	while (loaded_words < vpi.length) {
		// now get a handle on the current word we want in the array that was passed to us
		array_word = vpi_handle_by_index(argh, loaded_words);

		if (array_word != NULL) {
			argval.value.integer = (uint32_t)vpi.buffer_out[loaded_words];
			// And vpi_put_value() it back into the sim
			vpi_put_value(array_word, &argval, NULL, vpiNoDelay);
		} else
			return;

		loaded_words++;
	}

/*******************************************/

	// Cleanup and return
	vpi_free_object(args_iter);

}

void send_result_to_server(char *userdata){

	vpiHandle systfref, args_iter, argh;
	struct t_vpi_value argval;
	int n;
	struct vpi_cmd vpi;

	uint32_t length;
	int sent_words;

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

	// check we got passed a memory (array of regs)
	if (!((vpi_get(vpiType, argh) == vpiMemory)
#ifdef MODELSIM_VPI
	|| (vpi_get(vpiType, argh) == vpiRegArray)
#endif
	)) {
		vpi_printf("jp_vpi: ERROR: did not pass a memory to get_command_block_data\n");
		vpi_printf("jp_vpi: ERROR: was passed type %d\n", (int)vpi_get(vpiType, argh));
		return;
	}

	// check the memory we're writing into is big enough
	if (vpi_get(vpiSize, argh) < length ) {
		vpi_printf("jp_vpi: ERROR: buffer passed to get_command_block_data too small. size is %d words, needs to be %d\n",
		 vpi_get(vpiSize, argh), length);
		return;
	}

	// Loop to load the words
	sent_words = 0;
	while (sent_words < length) {
		// Get a handle on the current word we want in the array that was passed to us
		array_word = vpi_handle_by_index(argh, sent_words);

		if (array_word != NULL) {
			vpi_get_value(array_word, &argval);
			vpi.buffer_in[sent_words] = (uint32_t) argval.value.integer;
		} else
			return;

		sent_words++;
	}

	n = write(connfd, &vpi, sizeof(struct vpi_cmd));

	// Cleanup and return
	vpi_free_object(args_iter);
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

void register_send_result_to_server() {
  s_vpi_systf_data data = {vpiSysTask,
			   0,
			   "$send_result_to_server",
			   (void *)send_result_to_server,
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
  //init_jtag_server(RSP_SERVER_PORT); // Start the RSP server from here!

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
  close(connfd);
  close(listenfd);
}



// Register the new system task here
void (*vlog_startup_routines[ ] ) () = {
#ifdef CDS_VPI
  // this installs a callback on simulator reset - something which
  // icarus does not do, so we only do it for cadence currently
  setup_reset_callbacks,
#endif
  setup_endofcompile_callbacks,
  setup_finish_callbacks,
  register_check_for_command,
  register_send_result_to_server,
  0  // last entry must be 0
};



// Entry point for testing development of the vpi functions
int main(int argc, char *argv[])
{
	return 0;

}



