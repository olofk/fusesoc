// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0

`timescale 1ns/1ns

/**
 * "Testbench" for multiblinky
 *
 * This testbench doesn't perform any automated testing but it only useful for waveform viewers.
 */
module multiblinky_tb;
  parameter clk_freq_hz = 50_000;
  localparam clk_half_period = 1_000_000_000 / clk_freq_hz / 2;

  logic clk = 1'b1;
  logic rst_n = 1'b1;
  logic [63:0] leds;

  multiblinky #(
    .clk_freq_hz(clk_freq_hz)
  ) u_dut (
    .clk,
    .rst_n,
    .q (leds)
  );

  always #clk_half_period clk <= ~clk;

  initial begin
    rst_n = 1'b0;
    @(posedge clk);
    @(posedge clk);
    rst_n = 1'b1;

    #10s $finish();
  end

`ifdef __ICARUS__
  // Icarus Verilog requires explicit code to dump waveforms.
  initial begin
    $dumpfile ("multiblinky.fst");
    $dumpvars (0, u_dut);
  end
`endif
endmodule
