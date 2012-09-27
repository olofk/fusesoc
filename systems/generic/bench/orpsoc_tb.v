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
     if($value$plusargs("timeout=%d", timeout))
       #timeout $finish;
   
   orpsoc_top #(.memory_file("sram.vmem")) dut
     (.clk_pad_i   (clk),
      .rst_n_pad_i (rst_n)
      );

   or1200_monitor i_monitor
     (.clk (clk),
      .wb_insn (orpsoc_tb.dut.or1200_top0.or1200_cpu.or1200_ctrl.wb_insn)
      );
   
endmodule
