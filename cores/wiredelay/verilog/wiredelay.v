
`timescale 1ns / 1ps

module wiredelay # (
  parameter Delay_g = 0,
  parameter Delay_rd = 0
)
(
  inout A,
  inout B,
  input reset
);  

  reg A_r;
  reg B_r;
  reg line_en;

  assign A = A_r;
  assign B = B_r;

  always @(*) begin
    if (!reset) begin
      A_r <= 1'bz;
      B_r <= 1'bz;
      line_en <= 1'b0;
    end else begin 
      if (line_en) begin
        A_r <= #Delay_rd B;
	B_r <= 1'bz;
      end else begin
        B_r <= #Delay_g A;
	A_r <= 1'bz;
      end
    end
  end

  always @(A or B) begin
    if (!reset) begin
      line_en <= 1'b0;
    end else if (A !== A_r) begin
      line_en <= 1'b0;
    end else if (B_r !== B) begin
      line_en <= 1'b1;
    end else begin
      line_en <= line_en;
    end
  end
endmodule
