//////////////////////////////////////////////////////////////////////
// usbSerialInterfaceEngine_h.v                                
//////////////////////////////////////////////////////////////////////

`ifdef usbSerialInterfaceEngine_h_vdefined
`else
`define usbSerialInterfaceEngine_h_vdefined

 // Sampling frequency = 'FS_OVER_SAMPLE_RATE' * full speed bit rate = 'LS_OVER_SAMPLE_RATE' * low speed bit rate
`define FS_OVER_SAMPLE_RATE 4
`define LS_OVER_SAMPLE_RATE 32

//timeOuts
`define RX_PACKET_TOUT 18
`define RX_EDGE_DET_TOUT 7

//TXStreamControlTypes
`define TX_DIRECT_CONTROL 8'h00
`define TX_RESUME_START 8'h01
`define TX_PACKET_START 8'h02
`define TX_PACKET_STREAM 8'h03
`define TX_PACKET_STOP 8'h04
`define TX_IDLE 8'h05
`define TX_LS_KEEP_ALIVE 8'h06

//RXStreamControlTypes
`define RX_PACKET_START 0
`define RX_PACKET_STREAM 1
`define RX_PACKET_STOP 2

//USBLineStates
// ONE_ZERO corresponds to differential 1. ie D+ = Hi, D- = Lo
`define ONE_ZERO 2'b10
`define ZERO_ONE 2'b01
`define SE0 2'b00
`define SE1 2'b11

//RXStatusIndices
`define CRC_ERROR_BIT 0
`define BIT_STUFF_ERROR_BIT 1
`define RX_OVERFLOW_BIT 2
`define NAK_RXED_BIT 3
`define STALL_RXED_BIT 4
`define ACK_RXED_BIT 5
`define DATA_SEQUENCE_BIT 6

//usbWireControlStates
`define TRI_STATE 1'b0
`define DRIVE 1'b1

//limits
`define MAX_CONSEC_SAME_BITS 4'h6
`define MAX_CONSEC_SAME_BITS_PLUS1 4'h7
// RESUME_RX_WAIT_TIME defines the time period for resume detection
// The resume counter is incremented at the bit rate, so
// RESUME_RX_WAIT_TIME = 29 corresponds to 30 * 1/12MHz = 2.5uS at full speed
// and 30 * 1/1.5MHz =  20uS at low speed, both of which are within the USB spec of 
// 2.5uS <= resumeDetectTime <= 100uS
`define RESUME_RX_WAIT_TIME 5'd29
//`define RESUME_WAIT_TIME_MINUS1 9
// 'HOST_TX_RESUME_TIME' assumes counter is incremented at low speed bit rate 
`ifdef SIM_COMPILE 
`define HOST_TX_RESUME_TIME 16'd10
`else
`define HOST_TX_RESUME_TIME 16'd30000  //Host sends resume for 30000 * 1/1.5MHz = 20mS
`endif
//`define CONNECT_WAIT_TIME 8'd20
`define CONNECT_WAIT_TIME 8'd120      //Device connect detected after 120 * 1/48MHz = 2.5uS
//`define DISCONNECT_WAIT_TIME 8'd20   
`define DISCONNECT_WAIT_TIME 8'd120   //Device disconnect detected after 120 * 1/48MHz = 2.5uS

//RXConnectStates
`define DISCONNECT 2'b00
`define LOW_SPEED_CONNECT 2'b01
`define FULL_SPEED_CONNECT 2'b10

//TX_RX_InternalStreamTypes
`define DATA_START 8'h00
`define DATA_STOP 8'h01
`define DATA_STREAM 8'h02
`define DATA_BIT_STUFF_ERROR 8'h03

//RXStMach states
`define DISCONNECT_ST 4'h0
`define WAIT_FULL_SPEED_CONN_ST 4'h1
`define WAIT_LOW_SPEED_CONN_ST 4'h2
`define CONNECT_LOW_SPEED_ST 4'h3
`define CONNECT_FULL_SPEED_ST 4'h4
`define WAIT_LOW_SP_DISCONNECT_ST 4'h5
`define WAIT_FULL_SP_DISCONNECT_ST 4'h6

//RXBitStateMachStates
`define IDLE_BIT_ST 2'b00
`define DATA_RECEIVE_BIT_ST 2'b01
`define WAIT_RESUME_ST 2'b10
`define RESUME_END_WAIT_ST 2'b11

//RXByteStateMachStates 
`define IDLE_BYTE_ST 3'b000
`define CHECK_SYNC_ST 3'b001
`define CHECK_PID_ST 3'b010
`define HS_BYTE_ST 3'b011
`define TOKEN_BYTE_ST 3'b100
`define DATA_BYTE_ST 3'b101

`endif //usbSerialInterfaceEngine_h_vdefined


