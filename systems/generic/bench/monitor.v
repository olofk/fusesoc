module or1200_monitor
  (input clk,
   input [31:0] wb_insn);
   
   integer 	r3;
   
   always @(posedge clk) begin
      if (wb_insn == 32'h1500_0001) begin
	 r3 = orpsoc_tb.dut.or1200_top0.or1200_cpu.or1200_rf.rf_a.get_gpr(5'b00011);
	 $display("exit(%0d)",r3);
	 $finish;
      end
   end
endmodule
