module spi_bfm
  #(parameter sclk_period = 10)
   (output reg sclk_o = 1'b1,
    output reg mosi_o = 1'b0,
    input      miso_i,
    output reg cs_n_o = 1'b1);

   task send;
      input [7:0] value_i;
      input       cs_n_i;

      integer     idx;
      
      begin
         cs_n_o <= cs_n_i;
         for (idx = 0 ; idx<8 ; idx=idx+1) begin
            mosi_o <= value_i[idx];
            #(sclk_period/2) sclk_o <= 1'b0;
            #(sclk_period/2) sclk_o <= 1'b1;
         end
         cs_n_o <= 1'b1;
      end
   endtask
   
endmodule

                            
