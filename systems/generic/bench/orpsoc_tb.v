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
   ram_wb_loader ram_wb_loader0();

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
