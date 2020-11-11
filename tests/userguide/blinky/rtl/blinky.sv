// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0

`include "macros.svh"

/**
 * Blink the output |q| with a 1 second pulse.
 */
module blinky
#(
  parameter clk_freq_hz = 1_000_000_000
) (
  input        clk,
  input        rst_n,
  output logic q
);

  logic [`CLOG2(clk_freq_hz)-1:0] count;

  always_ff @(posedge clk) begin
    if (~rst_n) begin
      count <= 'd0;
      q <= 1'b0;
    end else begin
      if (count == clk_freq_hz - 1) begin
        q <= ~q;
        count <= 'd0;
      end else begin
        count <= count + 'd1;
      end
    end
  end

endmodule
