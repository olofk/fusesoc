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

   reg [1023:0] testcase;
   
   //FIXME: Add options for VCD logging
   initial begin
      $dumpfile("testlog.vcd");
      $dumpvars(0);
      if($value$plusargs("testcase=%s",testcase))
	$readmemh(testcase, dut.ram_wb0.ram_wb_b3_0.mem);
      else begin
	 $display("No testcase specified");
	 $finish;
      end
      
   end

   //Force simulation stop after timeout cycles
   reg [63:0] timeout;
   initial
     if($value$plusargs("timeout=%d", timeout)) begin
	#timeout $display("Timeout: Forcing end of simulation");
	$finish;
     end

   reg enable_dbg;
   initial
     enable_dbg = $test$plusargs("enable_dbg");
   
   wire uart;
   
   wire tms;
   wire tck;
   wire tdi;
   wire tdo;

   vpi_debug_module vpi_dbg
     (
      .tms(tms), 
      .tck(tck), 
      .tdi(tdi), 
      .tdo(tdo),
      .enable(enable_dbg)
      );

   orpsoc_top #(.memory_file("sram.vmem")) dut
     (.clk_pad_i   (clk),
      .rst_n_pad_i (rst_n),
      //JTAG interface
      .tms_pad_i(tms),
      .tck_pad_i(tck),
      .tdi_pad_i(tdi),
      .tdo_pad_o(tdo),
      //UART interface
      .uart0_srx_pad_i(uart),
      .uart0_stx_pad_o(uart)
      );

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
