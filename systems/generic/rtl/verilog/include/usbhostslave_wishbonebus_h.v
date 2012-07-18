//////////////////////////////////////////////////////////////////////
// wishBoneBus_h.v                                              
//////////////////////////////////////////////////////////////////////

`ifdef wishBoneBus_h_vdefined
`else
`define wishBoneBus_h_vdefined
 
//memoryMap
`define HCREG_BASE 8'h00
`define HCREG_BASE_PLUS_0X10 8'h10
`define HOST_RX_FIFO_BASE 8'h20
`define HOST_TX_FIFO_BASE 8'h30
`define SCREG_BASE 8'h40
`define SCREG_BASE_PLUS_0X10 8'h50
`define EP0_RX_FIFO_BASE 8'h60
`define EP0_TX_FIFO_BASE 8'h70
`define EP1_RX_FIFO_BASE 8'h80
`define EP1_TX_FIFO_BASE 8'h90
`define EP2_RX_FIFO_BASE 8'ha0
`define EP2_TX_FIFO_BASE 8'hb0
`define EP3_RX_FIFO_BASE 8'hc0
`define EP3_TX_FIFO_BASE 8'hd0
`define HOST_SLAVE_CONTROL_BASE 8'he0
`define ADDRESS_DECODE_MASK 8'hf0

//FifoAddresses
`define FIFO_DATA_REG 3'b000
`define FIFO_STATUS_REG 3'b001
`define FIFO_DATA_COUNT_MSB 3'b010
`define FIFO_DATA_COUNT_LSB 3'b011
`define FIFO_CONTROL_REG 3'b100

`endif //wishBoneBus_h_vdefined

