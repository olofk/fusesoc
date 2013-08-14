//#include "or1k-elf-loader.h"

#include "Vorpsoc_top__Syms.h"

#include "verilated.h"
#include "verilated_vcd_c.h"
extern "C" FILE* load_elf_file(char* elf_file_name);
extern "C" long get_size(FILE *bin_file);
extern "C" unsigned int read_32(FILE *bin_file, unsigned int address);

void parseArgs(int argc, char **argv);

int timeout = 0;
char *elf_file_name = NULL;

int main(int argc, char **argv, char **env) {
  Verilated::commandArgs(argc, argv);
  
  Vorpsoc_top* top = new Vorpsoc_top;

  bool done = false;
  if(argc > 1)
    parseArgs(argc, argv);
  uint32_t insn = 0;
  int t = 0;

  if(elf_file_name) {
    printf("Loading %s\n",elf_file_name);
    FILE *bin_file = load_elf_file(elf_file_name);
    if(bin_file == NULL) {
      printf("Error loading elf file\n");
      exit(1);
    }
    long size = get_size(bin_file);
    for(int i=0; i <size;i+=4) {
      top->v->wb_bfm_memory0->mem[i/4] = read_32(bin_file, i);
    }
  }

  top->wb_clk_i = 0;
  top->wb_rst_i = 1;

  Verilated::traceEverOn(true);
  VerilatedVcdC* tfp = new VerilatedVcdC;
  top->trace (tfp, 99);
  tfp->open ("simx.vcd");

  while(!done) {
    tfp->dump(t);
    top->eval();
    if(t>2) top->wb_rst_i = 0;
    top->wb_clk_i = !top->wb_clk_i;
    insn = top->v->or1200_top0->or1200_cpu->or1200_ctrl->wb_insn;
    if(insn == 0x15000001) {
      printf("Success! Got nop 0x1. Exiting\n");
      done = true;
    }
    if(timeout && t>timeout) {
      printf("Timeout reached\n");
      done = true;
    }
    t++;
  }
  tfp->close();
  exit(0);
}

void parseArgs(int argc, char **argv) {
  int i = 1;
  while (i < argc) {
    if (strcmp(argv[i], "--timeout") == 0) {
      i++;
      timeout = strtod(argv[i], NULL);
    } /*else if ((strcmp(argv[i], "-q") == 0) ||
	       (strcmp(argv[i], "--quiet") == 0)) {
	       quiet = true;
    }*/ else if (strcmp(argv[i], "--or1k-elf-load") == 0) {
      i++;
	elf_file_name = argv[i];
    } /*else if ((strcmp(argv[i], "-d") == 0) ||
	       (strcmp(argv[i], "--vcdfile") == 0) ||
	       (strcmp(argv[i], "-v") == 0) ||
	       (strcmp(argv[i], "--vcdon") == 0)
	       ) {
      VCD_enabled = true;
      dumping_now = true;
      vcdDumpFile = dumpNameDefault;
      if (i + 1 < argc)
	if (argv[i + 1][0] != '-') {
	  testNameString = argv[i + 1];
	  vcdDumpFile = testNameString;
	  i++;
	}
    } else if ((strcmp(argv[i], "-s") == 0) ||
	       (strcmp(argv[i], "--vcdstart") == 0)) {
      VCD_enabled = true;
      time_val = strtod(argv[i + 1], NULL);
      sc_time dump_start_time(time_val,
			      TIMESCALE_UNIT);
      dump_start = dump_start_time;
      dump_start_delay_set = true;
      dumping_now = false;
    } else if ((strcmp(argv[i], "-t") == 0) ||
	       (strcmp(argv[i], "--vcdstop") == 0)) {
      VCD_enabled = true;
      time_val = strtod(argv[i + 1], NULL);
      sc_time dump_stop_time(time_val,
			     TIMESCALE_UNIT);
      dump_stop = dump_stop_time;
      dump_stop_set = true;
    }
#ifdef JTAG_DEBUG
    else if ((strcmp(argv[i], "-r") == 0) ||
	     (strcmp(argv[i], "--rsp") == 0)) {
      rsp_server_enabled = true;
      if (i + 1 < argc)
	if (argv[i + 1][0] != '-') {
	  rsp_server_port =
	    atoi(argv[i + 1]);
	  i++;
	}
	}
	#endif*/
    else if ((strcmp(argv[i], "-h") == 0) ||
	     (strcmp(argv[i], "--help") == 0)) {
      printf("Usage: %s [options]\n", argv[0]);
      printf("\n  ORPSoCv3 cycle accurate model\n");
      printf
	("  For details visit http://opencores.org/openrisc,orpsocv2\n");
      printf("\n");
      printf("Options:\n");
      printf
	("  -h, --help\t\tPrint this help message\n");
      printf
	("  -q, --quiet\t\tDisable all except UART print out\n");
      printf("\nSimulation control:\n");
      printf
	("  -f, --program <file> \tLoad program from OR32 ELF <file>\n");
      printf
	("  --timeout <val> \tStop the sim at <val> ns\n");
      printf("\nVCD generation:\n");
      printf
	("  -v, --vcdon\t\tEnable VCD generation\n");
      printf
	("  -d, --vcdfile <file>\tEnable and save VCD to <file>\n");
      
      printf
	("  -s, --vcdstart <val>\tEnable and delay VCD generation until <val> ns\n");
      printf
	("  -t, --vcdstop <val> \tEnable and terminate VCD generation at <val> ns\n");
#ifdef JTAG_DEBUG
      printf("\nRemote debugging:\n");
      printf
	("  -r, --rsp [<port>]\tEnable RSP debugging server, opt. specify <port>\n");
#endif
      //monitor->printUsage();
      printf("\n");
      exit(0);
    }
    i++;
  }
}
