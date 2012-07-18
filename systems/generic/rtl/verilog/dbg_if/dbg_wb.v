//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_wb.v                                                    ////
////                                                              ////
////                                                              ////
////  This file is part of the SoC Debug Interface.               ////
////  http://www.opencores.org/projects/DebugInterface/           ////
////                                                              ////
////  Author(s):                                                  ////
////       Igor Mohor (igorm@opencores.org)                       ////
////                                                              ////
////                                                              ////
////  All additional information is avaliable in the README.txt   ////
////  file.                                                       ////
////                                                              ////
//////////////////////////////////////////////////////////////////////
////                                                              ////
//// Copyright (C) 2000 - 2004 Authors                            ////
////                                                              ////
//// This source file may be used and distributed without         ////
//// restriction provided that this copyright statement is not    ////
//// removed from the file and that any derivative work contains  ////
//// the original copyright notice and the associated disclaimer. ////
////                                                              ////
//// This source file is free software; you can redistribute it   ////
//// and/or modify it under the terms of the GNU Lesser General   ////
//// Public License as published by the Free Software Foundation; ////
//// either version 2.1 of the License, or (at your option) any   ////
//// later version.                                               ////
////                                                              ////
//// This source is distributed in the hope that it will be       ////
//// useful, but WITHOUT ANY WARRANTY; without even the implied   ////
//// warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR      ////
//// PURPOSE.  See the GNU Lesser General Public License for more ////
//// details.                                                     ////
////                                                              ////
//// You should have received a copy of the GNU Lesser General    ////
//// Public License along with this source; if not, download it   ////
//// from http://www.opencores.org/lgpl.shtml                     ////
////                                                              ////
//////////////////////////////////////////////////////////////////////

// synopsys translate_off
`include "timescale.v"
// synopsys translate_on
`include "dbg_wb_defines.v"

// Top module
module dbg_wb(
                // JTAG signals
                tck_i,
                tdi_i,
                tdo_o,

                // TAP states
                shift_dr_i,
                pause_dr_i,
                update_dr_i,

                wishbone_ce_i,
                crc_match_i,
                crc_en_o,
                shift_crc_o,
                rst_i,

                // WISHBONE common signals
                wb_clk_i,
                                                                                
                // WISHBONE master interface
                wb_adr_o, wb_dat_o, wb_dat_i, wb_cyc_o, wb_stb_o, wb_sel_o,
                wb_we_o, wb_ack_i, wb_cab_o, wb_err_i, wb_cti_o, wb_bte_o 

              );

// JTAG signals
input         tck_i;
input         tdi_i;
output        tdo_o;

// TAP states
input         shift_dr_i;
input         pause_dr_i;
input         update_dr_i;

input         wishbone_ce_i;
input         crc_match_i;
output        crc_en_o;
output        shift_crc_o;
input         rst_i;
// WISHBONE common signals
input         wb_clk_i;
                                                                                
// WISHBONE master interface
output [31:0] wb_adr_o;
output [31:0] wb_dat_o;
input  [31:0] wb_dat_i;
output        wb_cyc_o;
output        wb_stb_o;
output  [3:0] wb_sel_o;
output        wb_we_o;
input         wb_ack_i;
output        wb_cab_o;
input         wb_err_i;
output  [2:0] wb_cti_o;
output  [1:0] wb_bte_o;

reg           wb_cyc_o;

reg           tdo_o;

reg    [31:0] wb_dat_tmp, wb_dat_dsff;
reg    [31:0] wb_adr_dsff;
reg     [3:0] wb_sel_dsff;
reg           wb_we_dsff;
reg    [`DBG_WB_DR_LEN -1 :0] dr;
wire          enable;
wire          cmd_cnt_en;
reg     [`DBG_WB_CMD_CNT_WIDTH -1:0] cmd_cnt;
wire          cmd_cnt_end;
reg           cmd_cnt_end_q;
reg           addr_len_cnt_en;
reg     [5:0] addr_len_cnt;
wire          addr_len_cnt_end;
reg           addr_len_cnt_end_q;
reg           crc_cnt_en;
reg     [`DBG_WB_CRC_CNT_WIDTH -1:0] crc_cnt;
wire          crc_cnt_end;
reg           crc_cnt_end_q;
reg           data_cnt_en;
reg    [`DBG_WB_DATA_CNT_WIDTH:0] data_cnt;
reg    [`DBG_WB_DATA_CNT_LIM_WIDTH:0] data_cnt_limit;
wire          data_cnt_end;
reg           data_cnt_end_q;

reg           crc_match_reg;

reg    [`DBG_WB_ACC_TYPE_LEN -1:0] acc_type;
reg    [`DBG_WB_ADR_LEN -1:0] adr;
reg    [`DBG_WB_LEN_LEN -1:0] len;
reg    [`DBG_WB_LEN_LEN:0]    len_var;
reg           start_rd_tck;
reg           rd_tck_started;
reg           start_rd_csff;
reg           start_wb_rd;
reg           start_wb_rd_q;
reg           start_wr_tck;
reg           start_wr_csff;
reg           start_wb_wr;
reg           start_wb_wr_q;

reg           status_cnt_en;
wire          status_cnt_end;

wire          byte, half, long;
reg           byte_q, half_q, long_q;

reg [`DBG_WB_STATUS_CNT_WIDTH -1:0] status_cnt;

reg [`DBG_WB_STATUS_LEN -1:0] status;

reg           wb_error, wb_error_csff, wb_error_tck;
reg           wb_overrun, wb_overrun_csff, wb_overrun_tck;
reg           underrun_tck;

reg           busy_wb;
reg           busy_tck;
reg           wb_end;
reg           wb_end_rst;
reg           wb_end_rst_csff;
reg           wb_end_csff;
reg           wb_end_tck, wb_end_tck_q;
reg           busy_csff;
reg           latch_data;
reg           update_dr_csff, update_dr_wb;

reg           set_addr, set_addr_csff, set_addr_wb, set_addr_wb_q;
wire   [31:0] input_data;

wire          len_eq_0;
wire          crc_cnt_31;

reg     [1:0] ptr;
reg     [2:0] fifo_cnt;
wire          fifo_full;
wire          fifo_empty;
reg     [7:0] mem [0:3];
reg     [2:0] mem_ptr_dsff;
reg           wishbone_ce_csff;
reg           mem_ptr_init;
reg [`DBG_WB_CMD_LEN_INT -1: 0] curr_cmd;
wire          curr_cmd_go;
reg           curr_cmd_go_q;
wire          curr_cmd_wr_comm;
wire          curr_cmd_rd_comm;
wire          acc_type_read;
wire          acc_type_write;
wire          acc_type_8bit;
wire          acc_type_16bit;
wire          acc_type_32bit;


assign enable = wishbone_ce_i & shift_dr_i;
assign crc_en_o = enable & crc_cnt_end & (~status_cnt_end);
assign shift_crc_o = enable & status_cnt_end;  // Signals dbg module to shift out the CRC

assign curr_cmd_go      = (curr_cmd == `DBG_WB_GO) && cmd_cnt_end;
assign curr_cmd_wr_comm = (curr_cmd == `DBG_WB_WR_COMM) && cmd_cnt_end;
assign curr_cmd_rd_comm = (curr_cmd == `DBG_WB_RD_COMM) && cmd_cnt_end;

assign acc_type_read    = (acc_type == `DBG_WB_READ8  || acc_type == `DBG_WB_READ16  || acc_type == `DBG_WB_READ32);
assign acc_type_write   = (acc_type == `DBG_WB_WRITE8 || acc_type == `DBG_WB_WRITE16 || acc_type == `DBG_WB_WRITE32);

assign acc_type_8bit    = (acc_type == `DBG_WB_READ8  || acc_type == `DBG_WB_WRITE8);
assign acc_type_16bit   = (acc_type == `DBG_WB_READ16 || acc_type == `DBG_WB_WRITE16);
assign acc_type_32bit   = (acc_type == `DBG_WB_READ32 || acc_type == `DBG_WB_WRITE32);


// Selecting where to take the data from
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    ptr <=  2'h0;
  else if (update_dr_i)
    ptr <=  2'h0;
  else if (curr_cmd_go && acc_type_read && crc_cnt_31) // first latch
    ptr <=  ptr + 1'b1;
  else if (curr_cmd_go && acc_type_read && byte && (!byte_q))
    ptr <= ptr + 1'd1;
end
                                                                                           

// Shift register for shifting in and out the data
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      latch_data <=  1'b0;
      dr <=  {`DBG_WB_DR_LEN{1'b0}};
    end
  else if (curr_cmd_rd_comm && crc_cnt_31)  // Latching data (from iternal regs)
    begin
      dr[`DBG_WB_ACC_TYPE_LEN + `DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN -1:0] <=  {acc_type, adr, len};
    end
  else if (acc_type_read && curr_cmd_go && crc_cnt_31 && !busy_tck)  // Latchind first data (from WB)
    begin
      dr[31:0] <=  input_data[31:0];
      latch_data <=  1'b1;
    end
  else if (acc_type_read && curr_cmd_go && crc_cnt_end && !busy_tck && wb_end_tck_q)  
    begin
       // Had to wait for data from WB.
       dr[31:0] <=  input_data[31:0];
       latch_data <=  1'b1;
    end
  else if (acc_type_read && curr_cmd_go && crc_cnt_end && !busy_tck) // Latching data (from WB)
    begin
      if (acc_type == `DBG_WB_READ8)
        begin
          if(byte & (~byte_q))
            begin
              case (ptr)    // synthesis parallel_case
                2'b00 : dr[31:24] <=  input_data[31:24];
                2'b01 : dr[31:24] <=  input_data[23:16];
                2'b10 : dr[31:24] <=  input_data[15:8];
                2'b11 : dr[31:24] <=  input_data[7:0];
              endcase
              latch_data <=  1'b1;
            end
          else
            begin
	       if (enable) // jb
		 dr[31:24] <=  {dr[30:24], 1'b0};
              latch_data <=  1'b0;
            end
        end
      else if (acc_type == `DBG_WB_READ16)
        begin
          if(half & (~half_q))
            begin
              if (ptr[1])
                dr[31:16] <=  input_data[15:0];
              else
                dr[31:16] <=  input_data[31:16];
              latch_data <=  1'b1;
            end
          else
            begin
	       if (enable) // jb
		 dr[31:16] <=  {dr[30:16], 1'b0};
              latch_data <=  1'b0;
            end
        end
      else if (acc_type == `DBG_WB_READ32)
        begin
          if(long & (~long_q))
            begin
              dr[31:0] <=  input_data[31:0];
              latch_data <=  1'b1;
            end
          else
            begin
	       if (enable) // jb
		 dr[31:0] <=  {dr[30:0], 1'b0};
              latch_data <=  1'b0;
            end
        end
    end
  else if (enable && (!addr_len_cnt_end))
    begin
      dr <=  {dr[`DBG_WB_DR_LEN -2:0], tdi_i};
    end
end



assign cmd_cnt_en = enable & (~cmd_cnt_end);


// Command counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    cmd_cnt <=  {`DBG_WB_CMD_CNT_WIDTH{1'b0}};
  else if (update_dr_i)
    cmd_cnt <=  {`DBG_WB_CMD_CNT_WIDTH{1'b0}};
  else if (cmd_cnt_en)
    cmd_cnt <=  cmd_cnt + `DBG_WB_CMD_CNT_WIDTH'd1;
end


// Assigning current command
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    curr_cmd <=  {`DBG_WB_CMD_LEN_INT{1'b0}};
  else if (update_dr_i)
    curr_cmd <=  {`DBG_WB_CMD_LEN_INT{1'b0}};
  else if (cmd_cnt == (`DBG_WB_CMD_LEN_INT -1))
    curr_cmd <=  {dr[`DBG_WB_CMD_LEN_INT-2 :0], tdi_i};
end


// Assigning current command
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    curr_cmd_go_q <=  1'b0;
  else
    curr_cmd_go_q <=  curr_cmd_go;
end


always @ (enable or cmd_cnt_end or addr_len_cnt_end or curr_cmd_wr_comm or curr_cmd_rd_comm or crc_cnt_end)
begin
  if (enable && (!addr_len_cnt_end))
    begin
      if (cmd_cnt_end && curr_cmd_wr_comm)
        addr_len_cnt_en = 1'b1;
      else if (crc_cnt_end && curr_cmd_rd_comm)
        addr_len_cnt_en = 1'b1;
      else
        addr_len_cnt_en = 1'b0;
    end
  else
    addr_len_cnt_en = 1'b0;
end


// Address/length counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    addr_len_cnt <=  6'd0;
  else if (update_dr_i)
    addr_len_cnt <=  6'd0;
  else if (addr_len_cnt_en)
    addr_len_cnt <=  addr_len_cnt + 6'd1;
end


always @ (enable or data_cnt_end or cmd_cnt_end or curr_cmd_go or acc_type_write or acc_type_read or crc_cnt_end)
begin
  if (enable && (!data_cnt_end))
    begin
      if (cmd_cnt_end && curr_cmd_go && acc_type_write)
        data_cnt_en = 1'b1;
      else if (crc_cnt_end && curr_cmd_go && acc_type_read)
        data_cnt_en = 1'b1;
      else
        data_cnt_en = 1'b0;
    end
  else
    data_cnt_en = 1'b0;
end


// Data counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    data_cnt <=  {`DBG_WB_DATA_CNT_WIDTH+1{1'b0}};
  else if (update_dr_i)
    data_cnt <=  {`DBG_WB_DATA_CNT_WIDTH+1{1'b0}};
  else if (data_cnt_en)
    data_cnt <=  data_cnt + 1;
end



// Upper limit. Data counter counts until this value is reached.
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    data_cnt_limit <=  {`DBG_WB_DATA_CNT_LIM_WIDTH+1{1'b0}};
  else if (update_dr_i)
    data_cnt_limit <=  len + 1;
end


always @ (enable or crc_cnt_end or curr_cmd_rd_comm or curr_cmd_wr_comm or curr_cmd_go or addr_len_cnt_end or data_cnt_end or acc_type_write or acc_type_read or cmd_cnt_end)
begin
  if (enable && (!crc_cnt_end) && cmd_cnt_end)
    begin
      if (addr_len_cnt_end && curr_cmd_wr_comm)
        crc_cnt_en = 1'b1;
      else if (data_cnt_end && curr_cmd_go && acc_type_write)
        crc_cnt_en = 1'b1;
      else if (cmd_cnt_end && (curr_cmd_go && acc_type_read || curr_cmd_rd_comm))
        crc_cnt_en = 1'b1;
      else
        crc_cnt_en = 1'b0;
    end
  else
    crc_cnt_en = 1'b0;
end
   

// crc counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    crc_cnt <=  {`DBG_WB_CRC_CNT_WIDTH{1'b0}};
  else if(crc_cnt_en)
    crc_cnt <=  crc_cnt + 1;
  else if (update_dr_i)
    crc_cnt <=  {`DBG_WB_CRC_CNT_WIDTH{1'b0}};
end

assign cmd_cnt_end      = cmd_cnt      == `DBG_WB_CMD_LEN;
assign addr_len_cnt_end = addr_len_cnt == `DBG_WB_DR_LEN;
assign crc_cnt_end      = crc_cnt      == `DBG_WB_CRC_CNT_WIDTH'd32;
assign crc_cnt_31       = crc_cnt      == `DBG_WB_CRC_CNT_WIDTH'd31;
assign data_cnt_end     = (data_cnt    == {data_cnt_limit, 3'b000});

always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      crc_cnt_end_q       <=  1'b0;
      cmd_cnt_end_q       <=  1'b0;
      data_cnt_end_q      <=  1'b0;
      addr_len_cnt_end_q  <=  1'b0;
    end
  else
    begin
      crc_cnt_end_q       <=  crc_cnt_end;
      cmd_cnt_end_q       <=  cmd_cnt_end;
      data_cnt_end_q      <=  data_cnt_end;
      addr_len_cnt_end_q  <=  addr_len_cnt_end;
    end
end


// Status counter is made of 4 serialy connected registers
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    status_cnt <=  {`DBG_WB_STATUS_CNT_WIDTH{1'b0}};
  else if (update_dr_i)
    status_cnt <=  {`DBG_WB_STATUS_CNT_WIDTH{1'b0}};
  else if (status_cnt_en)
    status_cnt <=  status_cnt + `DBG_WB_STATUS_CNT_WIDTH'd1;
end


always @ (enable or status_cnt_end or crc_cnt_end or curr_cmd_rd_comm or curr_cmd_wr_comm or curr_cmd_go or acc_type_write or acc_type_read or data_cnt_end or addr_len_cnt_end)
begin
  if (enable && (!status_cnt_end))
    begin
      if (crc_cnt_end && curr_cmd_wr_comm)
        status_cnt_en = 1'b1;
      else if (crc_cnt_end && curr_cmd_go && acc_type_write)
        status_cnt_en = 1'b1;
      else if (data_cnt_end && curr_cmd_go && acc_type_read)
        status_cnt_en = 1'b1;
      else if (addr_len_cnt_end && curr_cmd_rd_comm)
        status_cnt_en = 1'b1;
      else
        status_cnt_en = 1'b0;
    end
  else
    status_cnt_en = 1'b0;
end


assign status_cnt_end = status_cnt == `DBG_WB_STATUS_LEN;


// Latching acc_type, address and length
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      acc_type  <=  {`DBG_WB_ACC_TYPE_LEN{1'b0}};
      adr       <=  {`DBG_WB_ADR_LEN{1'b0}};
      len       <=  {`DBG_WB_LEN_LEN{1'b0}};
      set_addr  <=  1'b0;
    end
  else if(crc_cnt_end && (!crc_cnt_end_q) && crc_match_i && curr_cmd_wr_comm)
    begin
      acc_type  <=  dr[`DBG_WB_ACC_TYPE_LEN + `DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN -1 : `DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN];
      adr       <=  dr[`DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN -1 : `DBG_WB_LEN_LEN];
      len       <=  dr[`DBG_WB_LEN_LEN -1:0];
      set_addr  <=  1'b1;
    end
  else if(wb_end_tck)               // Writing back the address
    begin
      adr  <=  wb_adr_dsff;
    end
  else
    set_addr <=  1'b0;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    crc_match_reg <=  1'b0;
  else if(crc_cnt_end & (~crc_cnt_end_q))
    crc_match_reg <=  crc_match_i;
end

// Length counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    len_var <=  {1'b0, {`DBG_WB_LEN_LEN{1'b0}}};
  else if(update_dr_i)
    len_var <=  len + 1;
  else if (start_rd_tck)
    begin
      case (acc_type)  // synthesis parallel_case
        `DBG_WB_READ8 : 
                    if (len_var > 'd1)
                      len_var <=  len_var - 1;
                    else
                      len_var <=  {1'b0, {`DBG_WB_LEN_LEN{1'b0}}};
        `DBG_WB_READ16: 
                    if (len_var > 'd2)
                      len_var <=  len_var - 2; 
                    else
                      len_var <=  {1'b0, {`DBG_WB_LEN_LEN{1'b0}}};
        `DBG_WB_READ32: 
                    if (len_var > 'd4)
                      len_var <=  len_var - 4; 
                    else
                      len_var <=  {1'b0, {`DBG_WB_LEN_LEN{1'b0}}};
        default:      len_var <=  {1'bx, {`DBG_WB_LEN_LEN{1'bx}}};
      endcase
    end
end


assign len_eq_0 = !(|len_var);
   


assign byte = data_cnt[2:0] == 3'd7;
assign half = data_cnt[3:0] == 4'd15;
assign long = data_cnt[4:0] == 5'd31;


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      byte_q <=   1'b0;
      half_q <=   1'b0;
      long_q <=   1'b0;
    end
  else
    begin
      byte_q <=  byte;
      half_q <=  half;
      long_q <=  long;
    end
end


// Start wishbone write cycle
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      start_wr_tck <=  1'b0;
      wb_dat_tmp <=  32'h0;
    end
  else if (curr_cmd_go && acc_type_write)
    begin
      case (acc_type)  // synthesis parallel_case full_case
        `DBG_WB_WRITE8  : begin
                        if (byte_q)
                          begin
                            start_wr_tck <=  1'b1;
                            wb_dat_tmp <=  {4{dr[7:0]}};
                          end
                        else
                          begin
                            start_wr_tck <=  1'b0;
                          end
                      end
        `DBG_WB_WRITE16 : begin
                        if (half_q)
                          begin
                            start_wr_tck <=  1'b1;
                            wb_dat_tmp <=  {2{dr[15:0]}};
                          end
                        else
                          begin
                            start_wr_tck <=  1'b0;
                          end
                      end
        `DBG_WB_WRITE32 : begin
                        if (long_q)
                          begin
                            start_wr_tck <=  1'b1;
                            wb_dat_tmp <=  dr[31:0];
                          end
                        else
                          begin
                            start_wr_tck <=  1'b0;
                          end
                       end
	default: begin

	end
      endcase
    end
  else
    start_wr_tck <=  1'b0;
end


// wb_dat_o in WB clk domain
always @ (posedge wb_clk_i)
begin
  wb_dat_dsff <=  wb_dat_tmp;
end

assign wb_dat_o = wb_dat_dsff;


// Start wishbone read cycle
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    start_rd_tck <=  1'b0;
  else if (curr_cmd_go && (!curr_cmd_go_q) && acc_type_read)              // First read after cmd is entered
    start_rd_tck <=  1'b1;
  else if ((!start_rd_tck) && curr_cmd_go && acc_type_read  && (!len_eq_0) && (!fifo_full) && (!rd_tck_started))
    start_rd_tck <=  1'b1;
  else
    start_rd_tck <=  1'b0;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    rd_tck_started <=  1'b0;
  else if (update_dr_i || wb_end_tck && (!wb_end_tck_q))
    rd_tck_started <=  1'b0;
  else if (start_rd_tck)
    rd_tck_started <=  1'b1;
end



always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      start_rd_csff   <=  1'b0;
      start_wb_rd     <=  1'b0;
      start_wb_rd_q   <=  1'b0;

      start_wr_csff   <=  1'b0;
      start_wb_wr     <=  1'b0;
      start_wb_wr_q   <=  1'b0;

      set_addr_csff   <=  1'b0;
      set_addr_wb     <=  1'b0;
      set_addr_wb_q   <=  1'b0;
    end
  else
    begin
      start_rd_csff   <=  start_rd_tck;
      start_wb_rd     <=  start_rd_csff;
      start_wb_rd_q   <=  start_wb_rd;

      start_wr_csff   <=  start_wr_tck;
      start_wb_wr     <=  start_wr_csff;
      start_wb_wr_q   <=  start_wb_wr;

      set_addr_csff   <=  set_addr;
      set_addr_wb     <=  set_addr_csff;
      set_addr_wb_q   <=  set_addr_wb;
    end
end


// wb_cyc_o
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_cyc_o <=  1'b0;
  else if ((start_wb_wr && (!start_wb_wr_q)) || (start_wb_rd && (!start_wb_rd_q)))
    wb_cyc_o <=  1'b1;
  else if (wb_ack_i || wb_err_i)
    wb_cyc_o <=  1'b0;
end


// wb_adr_o logic
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_adr_dsff <=  32'd0;
  else if (set_addr_wb && (!set_addr_wb_q)) // Setting starting address
    wb_adr_dsff <=  adr;
  else if (wb_ack_i)
    begin
      if ((acc_type == `DBG_WB_WRITE8) || (acc_type == `DBG_WB_READ8))
        wb_adr_dsff <=  wb_adr_dsff + 32'd1;
      else if ((acc_type == `DBG_WB_WRITE16) || (acc_type == `DBG_WB_READ16))
        wb_adr_dsff <=  wb_adr_dsff + 32'd2;
      else
        wb_adr_dsff <=  wb_adr_dsff + 32'd4;
    end
end


assign wb_adr_o = wb_adr_dsff;


//    adr   byte  |  short  |  long
//     0    1000     1100      1111
//     1    0100     err       err
//     2    0010     0011      err
//     3    0001     err       err
// wb_sel_o logic

always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_sel_dsff[3:0] <=  4'h0;
  else if ((start_wb_wr && (!start_wb_wr_q)))
    begin
      case ({wb_adr_dsff[1:0], acc_type_8bit, acc_type_16bit, acc_type_32bit}) // synthesis parallel_case
        {2'd0, 3'b100} : wb_sel_dsff[3:0] <=  4'h8;
        {2'd0, 3'b010} : wb_sel_dsff[3:0] <=  4'hC;
        {2'd0, 3'b001} : wb_sel_dsff[3:0] <=  4'hF;
        {2'd1, 3'b100} : wb_sel_dsff[3:0] <=  4'h4;
        {2'd2, 3'b100} : wb_sel_dsff[3:0] <=  4'h2;
        {2'd2, 3'b010} : wb_sel_dsff[3:0] <=  4'h3;
        {2'd3, 3'b100} : wb_sel_dsff[3:0] <=  4'h1;
        default:         wb_sel_dsff[3:0] <=  4'hx;
      endcase
    end
end


assign wb_sel_o = wb_sel_dsff;

/*
always @ (posedge wb_clk_i)
begin
  wb_we_dsff <=  curr_cmd_go && acc_type_write;
end
*/

always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
     wb_we_dsff <=  1'b0;
  else if ((start_wb_wr && (!start_wb_wr_q)))
    wb_we_dsff <=  1'b1;
  else if (wb_ack_i || wb_err_i)
    wb_we_dsff <=  1'b0;
end


assign wb_we_o = wb_we_dsff;
assign wb_cab_o = 1'b0;
assign wb_stb_o = wb_cyc_o;
assign wb_cti_o = 3'h0;     // always performing single access
assign wb_bte_o = 2'h0;     // always performing single access
                                                                                               
                                                                                               
                                                                                               
// Logic for detecting end of transaction
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_end <=  1'b0;
  else if (wb_ack_i || wb_err_i)
    wb_end <=  1'b1;
  else if (wb_end_rst)
    wb_end <=  1'b0;
end
                                                                                               
                                                                                               
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      wb_end_csff  <=  1'b0;
      wb_end_tck   <=  1'b0;
      wb_end_tck_q <=  1'b0;
    end
  else
    begin
      wb_end_csff  <=  wb_end;
      wb_end_tck   <=  wb_end_csff;
      wb_end_tck_q <=  wb_end_tck;
    end
end


always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      wb_end_rst_csff <=  1'b0;
      wb_end_rst      <=  1'b0;
    end
  else
    begin
      wb_end_rst_csff <=  wb_end_tck;
      wb_end_rst      <=  wb_end_rst_csff;
    end
end


always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    busy_wb <=  1'b0;
  else if (wb_end_rst)
    busy_wb <=  1'b0;
  else if (wb_cyc_o)
    busy_wb <=  1'b1;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      busy_csff       <=  1'b0;
      busy_tck        <=  1'b0;

      update_dr_csff  <=  1'b0;
      update_dr_wb    <=  1'b0;
    end
  else
    begin
      busy_csff       <=  busy_wb;
      busy_tck        <=  busy_csff;

      update_dr_csff  <=  update_dr_i;
      update_dr_wb    <=  update_dr_csff;
    end
end


// Detecting WB error
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_error <=  1'b0;
  else if(wb_err_i)
    wb_error <=  1'b1;
  else if(update_dr_wb) // error remains active until update_dr arrives
    wb_error <=  1'b0;
end


// Detecting overrun when write operation.
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    wb_overrun <=  1'b0;
  else if(start_wb_wr && (!start_wb_wr_q) && wb_cyc_o)
    wb_overrun <=  1'b1;
  else if(update_dr_wb) // error remains active until update_dr arrives
    wb_overrun <=  1'b0;
end


// Detecting underrun when read operation
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    underrun_tck <=  1'b0;
  else if(latch_data && fifo_empty && (!data_cnt_end))
    underrun_tck <=  1'b1;
  else if(update_dr_i) // error remains active until update_dr arrives
    underrun_tck <=  1'b0;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      wb_error_csff   <=  1'b0;
      wb_error_tck    <=  1'b0;

      wb_overrun_csff <=  1'b0;
      wb_overrun_tck  <=  1'b0;
    end
  else
    begin
      wb_error_csff   <=  wb_error;
      wb_error_tck    <=  wb_error_csff;

      wb_overrun_csff <=  wb_overrun;
      wb_overrun_tck  <=  wb_overrun_csff;
    end
end



always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      wishbone_ce_csff  <=  1'b0;
      mem_ptr_init      <=  1'b0;
    end
  else
    begin
      wishbone_ce_csff  <=   wishbone_ce_i;
      mem_ptr_init      <=  ~wishbone_ce_csff;
    end
end


// Logic for latching data that is read from wishbone
always @ (posedge wb_clk_i or posedge rst_i)
begin
  if (rst_i)
    mem_ptr_dsff <=  3'h0;
  else if(mem_ptr_init)
    mem_ptr_dsff <=  3'h0;
  else if (wb_ack_i)
    begin
      if (acc_type == `DBG_WB_READ8)
        mem_ptr_dsff <=  mem_ptr_dsff + 3'd1;
      else if (acc_type == `DBG_WB_READ16)
        mem_ptr_dsff <=  mem_ptr_dsff + 3'd2;
    end
end


// Logic for latching data that is read from wishbone
always @ (posedge wb_clk_i)
begin
  if (wb_ack_i)
    begin
      case (wb_sel_dsff)    // synthesis parallel_case
        4'b1000  :  mem[mem_ptr_dsff[1:0]] <=  wb_dat_i[31:24];// byte
        4'b0100  :  mem[mem_ptr_dsff[1:0]] <=  wb_dat_i[23:16];// byte
        4'b0010  :  mem[mem_ptr_dsff[1:0]] <=  wb_dat_i[15:08];// byte
        4'b0001  :  mem[mem_ptr_dsff[1:0]] <=  wb_dat_i[07:00];// byte
        
	4'b1100  :                                                  // half
                    begin
                      mem[mem_ptr_dsff[1:0]]      <=  wb_dat_i[31:24];
                      mem[mem_ptr_dsff[1:0]+1'b1] <=  wb_dat_i[23:16];
                    end
        4'b0011  :                                                      // half
                    begin
                      mem[mem_ptr_dsff[1:0]]      <=  wb_dat_i[15:08];
                      mem[mem_ptr_dsff[1:0]+1'b1] <=  wb_dat_i[07:00];
                    end
        /*4'b1111  :                                                      // long*/
	default:
                    begin
                      mem[0] <=  wb_dat_i[31:24];
                      mem[1] <=  wb_dat_i[23:16];
                      mem[2] <=  wb_dat_i[15:08];
                      mem[3] <=  wb_dat_i[07:00];
                    end
	/*
        default  :                                                      // long
                    begin
                      mem[0] <=  8'hxx;
                      mem[1] <=  8'hxx;
                      mem[2] <=  8'hxx;
                      mem[3] <=  8'hxx;
                    end
	 */
      endcase
    end
end



assign input_data = {mem[0], mem[1], mem[2], mem[3]};


// Fifo counter and empty/full detection
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    fifo_cnt <=  3'h0;
  else if (update_dr_i)
    fifo_cnt <=  3'h0;
  else if (wb_end_tck && (!wb_end_tck_q) && (!latch_data) && (!fifo_full))  // incrementing
    begin
      case (acc_type)  // synthesis parallel_case
        `DBG_WB_READ8 : fifo_cnt <=  fifo_cnt + 3'd1;
        `DBG_WB_READ16: fifo_cnt <=  fifo_cnt + 3'd2;
        `DBG_WB_READ32: fifo_cnt <=  fifo_cnt + 3'd4;
        default:        fifo_cnt <=  3'bxxx;
      endcase
    end
  else if (!(wb_end_tck && (!wb_end_tck_q)) && latch_data && (!fifo_empty))  // decrementing
    begin
      case (acc_type)  // synthesis parallel_case
        `DBG_WB_READ8 : fifo_cnt <=  fifo_cnt - 3'd1;
        `DBG_WB_READ16: fifo_cnt <=  fifo_cnt - 3'd2;
        `DBG_WB_READ32: fifo_cnt <=  fifo_cnt - 3'd4;
        default:        fifo_cnt <=  3'bxxx;
      endcase
    end
end


assign fifo_full  = fifo_cnt == 3'h4;
assign fifo_empty = fifo_cnt == 3'h0;


// TDO multiplexer
always @ (pause_dr_i or busy_tck or crc_cnt_end or crc_cnt_end_q or curr_cmd_wr_comm or 
          curr_cmd_rd_comm or curr_cmd_go or acc_type_write or acc_type_read or crc_match_i
          or data_cnt_end or dr or data_cnt_end_q or crc_match_reg or status_cnt_en or status 
          or addr_len_cnt_end or addr_len_cnt_end_q)
begin
  if (pause_dr_i)
    begin
    tdo_o = busy_tck;
    end
  else if (crc_cnt_end && (!crc_cnt_end_q) && (curr_cmd_wr_comm || curr_cmd_go && acc_type_write ))
    begin
      tdo_o = ~crc_match_i;
    end
  else if (curr_cmd_go && acc_type_read && crc_cnt_end && (!data_cnt_end))
    begin
      tdo_o = dr[31];
    end
  else if (curr_cmd_go && acc_type_read && data_cnt_end && (!data_cnt_end_q))
    begin
      tdo_o = ~crc_match_reg;
    end
  else if (curr_cmd_rd_comm && addr_len_cnt_end && (!addr_len_cnt_end_q))
    begin
      tdo_o = ~crc_match_reg;
    end
  else if (curr_cmd_rd_comm && crc_cnt_end && (!addr_len_cnt_end))
    begin
      tdo_o = dr[`DBG_WB_ACC_TYPE_LEN + `DBG_WB_ADR_LEN + `DBG_WB_LEN_LEN -1];
    end
  else if (status_cnt_en)
    begin
      tdo_o = status[3];
    end
  else
    begin
      tdo_o = 1'b0;
    end
end

// Status register
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
    status <=  {`DBG_WB_STATUS_LEN{1'b0}};
    end
  else if(crc_cnt_end && (!crc_cnt_end_q) && (!(curr_cmd_go && acc_type_read)))
    begin
    status <=  {1'b0, wb_error_tck, wb_overrun_tck, crc_match_i};
    end
  else if (data_cnt_end && (!data_cnt_end_q) && curr_cmd_go && acc_type_read)
    begin
    status <=  {1'b0, wb_error_tck, underrun_tck, crc_match_reg};
    end
  else if (addr_len_cnt_end && (!addr_len_cnt_end) && curr_cmd_rd_comm)
    begin
    status <=  {1'b0, 1'b0, 1'b0, crc_match_reg};
    end
  else if (shift_dr_i && (!status_cnt_end))
    begin
    status <=  {status[`DBG_WB_STATUS_LEN -2:0], status[`DBG_WB_STATUS_LEN -1]};
    end
end
// Following status is shifted out (MSB first):
// 3. bit:          1 if crc is OK, else 0
// 2. bit:          1'b0
// 1. bit:          1 if WB error occured, else 0
// 0. bit:          1 if overrun occured during write (data couldn't be written fast enough)
//                    or underrun occured during read (data couldn't be read fast enough)


endmodule

