module or1200_monitor
  (input clk,
   input wb_insn)

  always @(posedge clk) begin
     if (wb_insn == 32'h1500_0001) begin
	$display("Ending simulation");
	$finish;
     end
  end
endmodule
