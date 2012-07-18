//////////////////////////////////////////////////////////////////////
//// usbConstants_h.v                                             
///////////////////////////////////////////////////////////////////////

`ifdef usbConstants_h_vdefined
`else
`define usbConstants_h_vdefined

//PIDTypes
`define OUT 4'h1
`define IN 4'h9
`define SOF 4'h5
`define SETUP 4'hd
`define DATA0 4'h3
`define DATA1 4'hb
`define ACK 4'h2
`define NAK 4'ha
`define STALL 4'he
`define PREAMBLE 4'hc 
     

//PIDGroups
`define SPECIAL 2'b00
`define TOKEN 2'b01
`define HANDSHAKE 2'b10
`define DATA 2'b11

// start of packet SyncByte
`define SYNC_BYTE 8'h80

`endif //usbConstants_h_vdefined       

