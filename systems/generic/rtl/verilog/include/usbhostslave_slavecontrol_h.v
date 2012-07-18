//////////////////////////////////////////////////////////////////////
// usbSlaveControl.v                                           
//////////////////////////////////////////////////////////////////////

`ifdef usbSlaveControl_h_vdefined
`else
`define usbSlaveControl_h_vdefined

//endPointConstants 
`define NUM_OF_ENDPOINTS 4
`define NUM_OF_REGISTERS_PER_ENDPOINT 4
`define BASE_INDEX_FOR_ENDPOINT_REGS 0
`define ENDPOINT_CONTROL_REG 0
`define ENDPOINT_STATUS_REG 1
`define ENDPOINT_TRANSTYPE_STATUS_REG 2
`define NAK_TRANSTYPE_STATUS_REG 3
`define EP0_CTRL_REG 5'h0
`define EP0_STS_REG 5'h1
`define EP0_TRAN_TYPE_STS_REG 5'h2
`define EP0_NAK_TRAN_TYPE_STS_REG 5'h3
`define EP1_CTRL_REG 5'h4
`define EP1_STS_REG 5'h5
`define EP1_TRAN_TYPE_STS_REG 5'h6
`define EP1_NAK_TRAN_TYPE_STS_REG 5'h7
`define EP2_CTRL_REG 5'h8
`define EP2_STS_REG 5'h9
`define EP2_TRAN_TYPE_STS_REG 5'ha
`define EP2_NAK_TRAN_TYPE_STS_REG 5'hb
`define EP3_CTRL_REG 5'hc
`define EP3_STS_REG 5'hd
`define EP3_TRAN_TYPE_STS_REG 5'he
`define EP3_NAK_TRAN_TYPE_STS_REG 5'hf


//SCRegIndices 
`define LAST_ENDP_REG = `BASE_INDEX_FOR_ENDPOINT_REGS + (`NUM_OF_REGISTERS_PER_ENDPOINT * `NUM_OF_ENDPOINTS) - 1
`define SC_CONTROL_REG 5'h10
`define SC_LINE_STATUS_REG 5'h11
`define SC_INTERRUPT_STATUS_REG 5'h12
`define SC_INTERRUPT_MASK_REG 5'h13
`define SC_ADDRESS 5'h14
`define SC_FRAME_NUM_MSP 5'h15
`define SC_FRAME_NUM_LSP 5'h16
`define SCREG_BUFFER_LEN 5'h17
//SCRXStatusRegIndices 
`define NAK_SET_MASK 8'h10
`define SC_CRC_ERROR_BIT 0
`define SC_BIT_STUFF_ERROR_BIT 1
`define SC_RX_OVERFLOW_BIT 2
`define SC_RX_TIME_OUT_BIT 3
`define SC_NAK_SENT_BIT 4
`define SC_STALL_SENT_BIT 5
`define SC_ACK_RXED_BIT 6
`define SC_DATA_SEQUENCE_BIT 7
//SCEndPointControlRegIndices 
`define ENDPOINT_ENABLE_BIT 0
`define ENDPOINT_READY_BIT 1
`define ENDPOINT_OUTDATA_SEQUENCE_BIT 2
`define ENDPOINT_SEND_STALL_BIT 3
`define ENDPOINT_ISO_ENABLE_BIT 4
//SCMasterControlegIndices 
`define SC_GLOBAL_ENABLE_BIT 0
`define SC_TX_LINE_STATE_LSBIT 1
`define SC_TX_LINE_STATE_MSBIT 2
`define SC_DIRECT_CONTROL_BIT 3
`define SC_FULL_SPEED_LINE_POLARITY_BIT 4
`define SC_FULL_SPEED_LINE_RATE_BIT 5
`define SC_CONNECT_TO_HOST_BIT 6
//SCinterruptRegIndices 
`define TRANS_DONE_BIT 0
`define RESUME_INT_BIT 1
`define RESET_EVENT_BIT 2  //Line has entered reset state or left reset state
`define SOF_RECEIVED_BIT 3
`define NAK_SENT_INT_BIT 4
`define VBUS_DET_INT_BIT 5
//TXTransactionTypes 
`define SC_SETUP_TRANS 0
`define SC_IN_TRANS 1
`define SC_OUTDATA_TRANS 2
//timeOuts 
`define SC_RX_PACKET_TOUT 18

//line status reg
`define VBUS_PRES_BIT 2

`endif //usbSlaveControl_h_vdefined  
