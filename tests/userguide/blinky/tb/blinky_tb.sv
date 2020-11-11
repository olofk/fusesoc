// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0

`timescale 1ns / 1ns

module blinky_tb;
  parameter clk_freq_hz = 50_000;
  parameter pulses = 5;

  localparam clk_half_period = 1_000_000_000 / clk_freq_hz / 2;

  logic clk = 1'b1;
  logic rst_n = 1'b1;
  logic led;

  blinky #(
    .clk_freq_hz(clk_freq_hz)
  ) u_dut (
    .clk,
    .rst_n,
    .q (led)
  );

  always #clk_half_period clk <= ~clk;

  time last_edge = 0;

  initial begin
    rst_n = 1'b0;
    @(posedge clk);
    @(posedge clk);
    rst_n = 1'b1;

    @(posedge clk);

    for (int i = 0; i < pulses; i = i + 1) begin
      @(led);
      last_edge = $time;

      @(led);
      if (($time - last_edge) != 1_000_000_000) begin
        $display("Error! Length of pulse was %0d ns, expected 1 s.", $time - last_edge);
        $finish;
      end else begin
        $display("Pulse %0d/%0d OK!", i + 1, pulses);
      end
    end

    $display("Testbench finished OK");
    $finish;
  end
endmodule
