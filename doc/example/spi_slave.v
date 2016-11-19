/*
 This is a simple SPI slave to GPIO bridge. It has a clock input, a synchronous
 reset input, an SPI slave interface which is supposed to be hooked up to an SPI
 master and an 8-bit output register. The contents of the output register is
 updated by doing a one byte SPI transaction. A bit is registered every time
 there is a falling edge on sclk and cs_n is deasserted.
 */

module spi_slave
  #(parameter INIT_VALUE = 8'd0)
   (
    input            clk,
    input            rst,
    input            sclk_i,
    input            mosi_i,
    output           miso_o = 1'b0,
    input            cs_n_i,
    output reg [7:0] gpio_o);

   reg     sclk_r;

   wire    sclk_edge = ~cs_n_i & sclk_r & ~sclk_i;

   reg [2:0] cnt;

   always @(posedge clk) begin
      sclk_r <= sclk_i;

      if (cs_n_i)
        cnt <= 3'd0;
      else if (sclk_edge) begin
         cnt <= cnt + 1'd1;
         gpio_o[cnt] <= mosi_i;
      end

      if (rst) begin
         cnt <= 3'd0;
         sclk_r <= 1'd1;
         gpio_o <= INIT_VALUE;
      end
   end
endmodule
