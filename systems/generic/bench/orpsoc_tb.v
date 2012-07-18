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
   initial begin
      $dumpfile("testlog.vcd");
      $dumpvars(0);
   end
   orpsoc_top dut
     (.clk_pad_i   (clk),
      .rst_n_pad_i (rst_n)
      );

   or1200_monitor i_monitor
     (.clk (clk),
      .wb_insn (orpsoc_tb.dut.or1200_top0.or1200_cpu.or1200_ctrl.wb_insn)
      );
   
endmodule
