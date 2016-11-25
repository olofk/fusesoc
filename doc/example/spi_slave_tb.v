module spi_slave_tb
  #(parameter transactions = 1000,
    parameter init_value = 8'h42);

   reg clk = 1'b1;
   reg rst = 1'b1;

   always #5 clk = ~clk;
   initial #100 rst = 1'b0;

   wire [7:0] gpio;

   vlog_tb_utils vtu();
   
   spi_bfm      #(.sclk_period (50))
bfm
     (.sclk_o (sclk),
      .mosi_o (mosi),
      .miso_i (1'b0),
      .cs_n_o (cs_n));

   spi_slave
     #(.INIT_VALUE (init_value))
   dut
     (.clk (clk),
      .rst (rst),
      .sclk_i (sclk),
      .mosi_i (mosi),
      .miso_o (),
      .cs_n_i (cs_n),
      .gpio_o (gpio));

   integer idx;
   integer seed = 1;
   
   reg [7:0] value = init_value;

   initial begin
      $display("Running %0d transactions", transactions);
      @(negedge rst);
      $display("Reset released");
      @(clk);
      
      for (idx=0 ; idx<transactions ; idx=idx+1 ) begin
         bfm.send(value, 1'b0);
         
         if (gpio != value) begin
            $display("Error in transaction %0d. Expected %02x. Got %02x", idx, value, gpio);
            $finish;
         end
	 value = $dist_uniform(seed, 0, 255);
      end
      $display("Test passed!");
      $finish;
   end

endmodule
