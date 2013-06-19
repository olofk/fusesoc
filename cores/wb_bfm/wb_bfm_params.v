localparam CLASSIC_CYCLE = 1'b0;
localparam BURST_CYCLE   = 1'b1;

localparam READ  = 1'b0;
localparam WRITE = 1'b1;
   
localparam LINEAR_BURST   = 3'd0;
localparam WRAP_4_BURST  = 3'd1;
localparam WRAP_8_BURST   = 3'd2;
localparam WRAP_16_BURST  = 3'd3;
localparam CONSTANT_BURST = 3'd4;
