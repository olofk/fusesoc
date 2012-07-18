//////////////////////////////////////////////////////////////////////
// usbHostControl_h.v                                          
//////////////////////////////////////////////////////////////////////

`ifdef usbHostControl_h_vdefined
`else
`define usbHostControl_h_vdefined

//HCRegIndices
`define TX_CONTROL_REG 4'h0
`define TX_TRANS_TYPE_REG 4'h1
`define TX_LINE_CONTROL_REG 4'h2
`define TX_SOF_ENABLE_REG 4'h3
`define TX_ADDR_REG 4'h4
`define TX_ENDP_REG 4'h5
`define FRAME_NUM_MSB_REG 4'h6
`define FRAME_NUM_LSB_REG 4'h7
`define INTERRUPT_STATUS_REG 4'h8
`define INTERRUPT_MASK_REG 4'h9
`define RX_STATUS_REG 4'ha
`define RX_PID_REG 4'hb
`define RX_ADDR_REG 4'hc
`define RX_ENDP_REG 4'hd
`define RX_CONNECT_STATE_REG 4'he
`define HOST_SOF_TIMER_MSB_REG 4'hf

`define HCREG_BUFFER_LEN 4'hf
`define HCREG_MASK 4'hf

//TXControlRegIndices
`define TRANS_REQ_BIT 0
`define SOF_SYNC_BIT 1
`define PREAMBLE_ENABLE_BIT 2
`define ISO_ENABLE_BIT 3

//interruptRegIndices
`define TRANS_DONE_BIT 0
`define RESUME_INT_BIT 1
`define CONNECTION_EVENT_BIT 2
`define SOF_SENT_BIT 3

//TXTransactionTypes
`define SETUP_TRANS 0
`define IN_TRANS 1
`define OUTDATA0_TRANS 2
`define OUTDATA1_TRANS 3
 
 //TXLineControlIndices
`define TX_LINE_STATE_LSBIT 0
`define TX_LINE_STATE_MSBIT 1
`define DIRECT_CONTROL_BIT 2
`define FULL_SPEED_LINE_POLARITY_BIT 3
`define FULL_SPEED_LINE_RATE_BIT 4

//TXSOFEnableIndices
`define SOF_EN_BIT 0

//SOFTimeConstants 
//`define SOF_TX_TIME 80     //Fix this. Need correct SOF TX interval   
//Note that 'SOF_TX_TIME' is 48000 - 3. This is to account for the delay in resetting the SOF timer 
`define SOF_TX_TIME 16'hbb7d     //Correct SOF interval for 48MHz clock.
//`define SOF_TX_MARGIN 2 
`define SOF_TX_MARGIN 16'h0190 //This is the transmission time for 100 bytes. May need to tweak
       
//Host RXStatusRegIndices 
`define HC_CRC_ERROR_BIT 0
`define HC_BIT_STUFF_ERROR_BIT 1
`define HC_RX_OVERFLOW_BIT 2
`define HC_RX_TIME_OUT_BIT 3
`define HC_NAK_RXED_BIT 4
`define HC_STALL_RXED_BIT 5
`define HC_ACK_RXED_BIT 6
`define HC_DATA_SEQUENCE_BIT 7

`endif //usbHostControl_h_vdefined 
