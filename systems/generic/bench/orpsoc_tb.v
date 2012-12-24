`include "timescale.v"

module orpsoc_tb;

   reg clk   = 0;
   reg rst_n = 1;

   always
     #5 clk <= ~clk;

   initial begin
      #100 rst_n <= 0;
      #200 rst_n <= 1;
   end

   vlog_tb_utils vlog_tb_utils0();

   integer mem_words;
   integer i;
   reg [31:0] mem_word;
   reg [1023:0] elf_file;

   initial begin
      if($value$plusargs("or1k_elf_load=%s", elf_file)) begin
	 $or1k_elf_load_file(elf_file);
      
	 mem_words = $or1k_elf_get_size/4;
	 for(i=0; i < mem_words; i = i+1)
	   orpsoc_tb.dut.ram_wb0.ram_wb_b3_0.mem[i] = $or1k_elf_read_32(i*4);
      end else
	$display("No ELF file specified");
   end
   
   reg enable_jtag_vpi;
   initial enable_jtag_vpi = $test$plusargs("enable_jtag_vpi");
   
   jtag_vpi jtag_vpi0
     (.tms       (tms),
      .tck       (tck),
      .tdi       (tdi),
      .tdo       (tdo),
      .enable    (enable_jtag_vpi),
      .init_done (orpsoc_tb.dut.wb_rst));

   orpsoc_top dut
     (.clk_pad_i   (clk),
      .rst_n_pad_i (rst_n),
      //JTAG interface
      .tms_pad_i(tms),
      .tck_pad_i(tck),
      .tdi_pad_i(tdi),
      .tdo_pad_o(tdo),
      //UART interface
      .uart0_srx_pad_i(uart),
      .uart0_stx_pad_o(uart));

   or1200_monitor i_monitor
     (.clk (clk),
      .wb_insn (orpsoc_tb.dut.or1200_top0.or1200_cpu.or1200_ctrl.wb_insn)
      );

   //FIXME: Get correct baud rate from parameter
   uart_decoder
     #(.uart_baudrate_period_ns(8680/2))
   uart_decoder0
     (.clk(clk),
      .uart_tx(uart));
   
endmodule
