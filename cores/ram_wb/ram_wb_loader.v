module ram_wb_loader;
   reg [1023:0] testcase;
   
   //FIXME: Don't hard code ram_wb location
   initial begin
      if($value$plusargs("testcase=%s",testcase))
	$readmemh(testcase, orpsoc_tb.dut.ram_wb0.ram_wb_b3_0.mem);
      else begin
	 $display("No testcase specified");
      end
   end
endmodule // ram_wb_loader

