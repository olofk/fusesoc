// This file is public domain, it can be freely copied without restrictions.
// SPDX-License-Identifier: CC0-1.0

`include "macros.svh"

/**
 * Blink two outputs q[0] and q[1].
 *
 * q[1] will blink twice as fast q[0].
 */
module dualblinky
#(
  parameter clk_freq_hz = 1_000_000_000
) (
  input              clk,
  input              rst_n,
  output logic [1:0] q
);

  // Instantiate the blinky module twice.

  blinky #(
    .clk_freq_hz(clk_freq_hz)
  ) u_blinky0 (
    .clk,
    .rst_n,
    .q (q[0])
  );

  blinky #(
    .clk_freq_hz(clk_freq_hz / 2) // Blink LED 1 twice as fast as LED 0.
  ) u_blinky1 (
    .clk,
    .rst_n,
    .q (q[1])
  );

endmodule
