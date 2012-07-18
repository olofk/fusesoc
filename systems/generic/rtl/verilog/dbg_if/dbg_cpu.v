//////////////////////////////////////////////////////////////////////
////                                                              ////
////  dbg_cpu.v                                                   ////
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
`include "dbg_cpu_defines.v"

// Top module
module dbg_cpu(
                // JTAG signals
                tck_i,
                tdi_i,
                tdo_o,

                // TAP states
                shift_dr_i,
                pause_dr_i,
                update_dr_i,

                cpu_ce_i,
                crc_match_i,
                crc_en_o,
                shift_crc_o,
                rst_i,

                // CPU
                cpu_clk_i,
                cpu_addr_o, cpu_data_i, cpu_data_o, cpu_bp_i, cpu_stall_o, 
                cpu_stb_o,
                cpu_we_o, cpu_ack_i, cpu_rst_o 

              );

// JTAG signals
input         tck_i;
input         tdi_i;
output        tdo_o;

// TAP states
input         shift_dr_i;
input         pause_dr_i;
input         update_dr_i;

input         cpu_ce_i;
input         crc_match_i;
output        crc_en_o;
output        shift_crc_o;
input         rst_i;

// CPU
input         cpu_clk_i;
output [31:0] cpu_addr_o;
output [31:0] cpu_data_o;
input         cpu_bp_i;
output        cpu_stall_o;
input  [31:0] cpu_data_i;
output        cpu_stb_o;
output        cpu_we_o;
input         cpu_ack_i;
output        cpu_rst_o;

reg           cpu_stb_o;
wire          cpu_reg_stall;
reg           tdo_o;
reg           cpu_ack_q;
reg           cpu_ack_csff;
reg           cpu_ack_tck;

reg    [31:0] cpu_dat_tmp, cpu_data_dsff;
reg    [31:0] cpu_addr_dsff;
reg           cpu_we_dsff;
reg    [`DBG_CPU_DR_LEN -1 :0] dr;
wire          enable;
wire          cmd_cnt_en;
reg     [`DBG_CPU_CMD_CNT_WIDTH -1:0] cmd_cnt;
wire          cmd_cnt_end;
reg           cmd_cnt_end_q;
reg           addr_len_cnt_en;
reg     [5:0] addr_len_cnt;
wire          addr_len_cnt_end;
reg           addr_len_cnt_end_q;
reg           crc_cnt_en;
reg     [`DBG_CPU_CRC_CNT_WIDTH -1:0] crc_cnt;
wire          crc_cnt_end;
reg           crc_cnt_end_q;
reg           data_cnt_en;
reg    [`DBG_CPU_DATA_CNT_WIDTH:0] data_cnt;
reg    [`DBG_CPU_DATA_CNT_LIM_WIDTH:0] data_cnt_limit;
wire          data_cnt_end;
reg           data_cnt_end_q;
reg           crc_match_reg;

reg    [`DBG_CPU_ACC_TYPE_LEN -1:0] acc_type;
reg    [`DBG_CPU_ADR_LEN -1:0] adr;
reg    [`DBG_CPU_LEN_LEN -1:0] len;
reg    [`DBG_CPU_LEN_LEN:0]    len_var;
wire   [`DBG_CPU_CTRL_LEN -1:0]ctrl_reg;
reg           start_rd_tck;
reg           rd_tck_started;
reg           start_rd_csff;
reg           start_cpu_rd;
reg           start_cpu_rd_q;
reg           start_wr_tck;
reg           start_wr_csff;
reg           start_cpu_wr;
reg           start_cpu_wr_q;

reg           status_cnt_en;
wire          status_cnt_end;

wire          half, long;
reg           half_q, long_q;

reg [`DBG_CPU_STATUS_CNT_WIDTH -1:0] status_cnt;

reg [`DBG_CPU_STATUS_LEN -1:0] status;

reg           cpu_overrun, cpu_overrun_csff, cpu_overrun_tck;
reg           underrun_tck;

reg           busy_cpu;
reg           busy_tck;
reg           cpu_end;
reg           cpu_end_rst;
reg           cpu_end_rst_csff;
reg           cpu_end_csff;
reg           cpu_end_tck, cpu_end_tck_q;
reg           busy_csff;
reg           latch_data;
reg           update_dr_csff, update_dr_cpu;
wire [`DBG_CPU_CTRL_LEN -1:0] cpu_reg_data_i;
wire                          cpu_reg_we;

reg           set_addr, set_addr_csff, set_addr_cpu, set_addr_cpu_q;
wire   [31:0] input_data;

wire          len_eq_0;
wire          crc_cnt_31;

reg           fifo_full;
reg     [7:0] mem [0:3];
reg           cpu_ce_csff;
reg           mem_ptr_init;
reg [`DBG_CPU_CMD_LEN -1: 0] curr_cmd;
wire          curr_cmd_go;
reg           curr_cmd_go_q;
wire          curr_cmd_wr_comm;
wire          curr_cmd_wr_ctrl;
wire          curr_cmd_rd_comm;
wire          curr_cmd_rd_ctrl;
wire          acc_type_read;
wire          acc_type_write;


assign enable = cpu_ce_i & shift_dr_i;
assign crc_en_o = enable & crc_cnt_end & (~status_cnt_end);
assign shift_crc_o = enable & status_cnt_end;  // Signals dbg module to shift out the CRC

assign curr_cmd_go      = (curr_cmd == `DBG_CPU_GO) && cmd_cnt_end;
assign curr_cmd_wr_comm = (curr_cmd == `DBG_CPU_WR_COMM) && cmd_cnt_end;
assign curr_cmd_wr_ctrl = (curr_cmd == `DBG_CPU_WR_CTRL) && cmd_cnt_end;
assign curr_cmd_rd_comm = (curr_cmd == `DBG_CPU_RD_COMM) && cmd_cnt_end;
assign curr_cmd_rd_ctrl = (curr_cmd == `DBG_CPU_RD_CTRL) && cmd_cnt_end;

assign acc_type_read    = (acc_type == `DBG_CPU_READ);
assign acc_type_write   = (acc_type == `DBG_CPU_WRITE);



// Shift register for shifting in and out the data
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      latch_data <=  1'b0;
      dr <=  {`DBG_CPU_DR_LEN{1'b0}};
    end
  else if (curr_cmd_rd_comm && crc_cnt_31)  // Latching data (from internal regs)
    begin
      dr[`DBG_CPU_DR_LEN -1:0] <=  {acc_type, adr, len};
    end
  else if (curr_cmd_rd_ctrl && crc_cnt_31)  // Latching data (from control regs)
    begin
      dr[`DBG_CPU_DR_LEN -1:0] <=  {ctrl_reg, {`DBG_CPU_DR_LEN -`DBG_CPU_CTRL_LEN{1'b0}}};
    end
  else if (acc_type_read && curr_cmd_go && crc_cnt_31)  // Latchind first data (from WB)
    begin
      dr[31:0] <=  input_data[31:0];
      latch_data <=  1'b1;
    end
  else if (acc_type_read && curr_cmd_go && crc_cnt_end) // Latching data (from WB)
    begin
      case (acc_type)  // synthesis parallel_case full_case
        `DBG_CPU_READ: begin
                      if(long & (~long_q))
                        begin
                          dr[31:0] <=  input_data[31:0];
                          latch_data <=  1'b1;
                        end
                      else if (enable)
                        begin
                          dr[31:0] <=  {dr[30:0], 1'b0};
                          latch_data <=  1'b0;
                        end
        end
	default: begin
	   
	end
      endcase
    end
  else if (enable && (!addr_len_cnt_end))
    begin
      dr <=  {dr[`DBG_CPU_DR_LEN -2:0], tdi_i};
    end
end



assign cmd_cnt_en = enable & (~cmd_cnt_end);


// Command counter
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    cmd_cnt <=  {`DBG_CPU_CMD_CNT_WIDTH{1'b0}};
  else if (update_dr_i)
    cmd_cnt <=  {`DBG_CPU_CMD_CNT_WIDTH{1'b0}};
  else if (cmd_cnt_en)
    cmd_cnt <=  cmd_cnt + 1;
end


// Assigning current command
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    curr_cmd <=  {`DBG_CPU_CMD_LEN{1'b0}};
  else if (update_dr_i)
    curr_cmd <=  {`DBG_CPU_CMD_LEN{1'b0}};
  else if (cmd_cnt == (`DBG_CPU_CMD_LEN -1))
    curr_cmd <=  {dr[`DBG_CPU_CMD_LEN-2 :0], tdi_i};
end


// Assigning current command
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    curr_cmd_go_q <=  1'b0;
  else
    curr_cmd_go_q <=  curr_cmd_go;
end


always @ (enable or cmd_cnt_end or addr_len_cnt_end or curr_cmd_wr_comm or curr_cmd_wr_ctrl or curr_cmd_rd_comm or curr_cmd_rd_ctrl or crc_cnt_end)
begin
  if (enable && (!addr_len_cnt_end))
    begin
      if (cmd_cnt_end && (curr_cmd_wr_comm || curr_cmd_wr_ctrl))
        addr_len_cnt_en = 1'b1;
      else if (crc_cnt_end && (curr_cmd_rd_comm || curr_cmd_rd_ctrl))
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
    addr_len_cnt <=  6'h0;
  else if (update_dr_i)
    addr_len_cnt <=  6'h0;
  else if (addr_len_cnt_en)
    addr_len_cnt <=  addr_len_cnt + 1;
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
    data_cnt <=  {`DBG_CPU_DATA_CNT_WIDTH+1{1'b0}};
  else if (update_dr_i)
    data_cnt <=  {`DBG_CPU_DATA_CNT_WIDTH+1{1'b0}};
  else if (data_cnt_en)
    data_cnt <=  data_cnt + 1;
end



// Upper limit. Data counter counts until this value is reached.
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    data_cnt_limit <=  {`DBG_CPU_DATA_CNT_LIM_WIDTH+1{1'b0}};
  else if (update_dr_i)
    data_cnt_limit <=  len + 1;
end


always @ (enable or crc_cnt_end or curr_cmd_rd_comm or curr_cmd_rd_ctrl or curr_cmd_wr_comm or curr_cmd_wr_ctrl or curr_cmd_go or addr_len_cnt_end or data_cnt_end or acc_type_write or acc_type_read or cmd_cnt_end)
begin
  if (enable && (!crc_cnt_end) && cmd_cnt_end)
    begin
      if (addr_len_cnt_end && (curr_cmd_wr_comm || curr_cmd_wr_ctrl))
        crc_cnt_en = 1'b1;
      else if (data_cnt_end && curr_cmd_go && acc_type_write)
        crc_cnt_en = 1'b1;
      else if (cmd_cnt_end && (curr_cmd_go && acc_type_read || curr_cmd_rd_comm || curr_cmd_rd_ctrl))
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
    crc_cnt <=  {`DBG_CPU_CRC_CNT_WIDTH{1'b0}};
  else if(crc_cnt_en)
    crc_cnt <=  crc_cnt + 1;
  else if (update_dr_i)
    crc_cnt <=  {`DBG_CPU_CRC_CNT_WIDTH{1'b0}};
end

assign cmd_cnt_end      = cmd_cnt      == `DBG_CPU_CMD_LEN;
assign addr_len_cnt_end = addr_len_cnt == `DBG_CPU_DR_LEN;
assign crc_cnt_end      = crc_cnt      == `DBG_CPU_CRC_CNT_WIDTH'd32;
assign crc_cnt_31       = crc_cnt      == `DBG_CPU_CRC_CNT_WIDTH'd31;
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
    status_cnt <=  {`DBG_CPU_STATUS_CNT_WIDTH{1'b0}};
  else if (update_dr_i)
    status_cnt <=  {`DBG_CPU_STATUS_CNT_WIDTH{1'b0}};
  else if (status_cnt_en)
    status_cnt <=  status_cnt + 1;
end


always @ (enable or status_cnt_end or crc_cnt_end or curr_cmd_rd_comm or curr_cmd_rd_ctrl or
          curr_cmd_wr_comm or curr_cmd_wr_ctrl or curr_cmd_go or acc_type_write or 
          acc_type_read or data_cnt_end or addr_len_cnt_end)
begin
  if (enable && (!status_cnt_end))
    begin
      if (crc_cnt_end && (curr_cmd_wr_comm || curr_cmd_wr_ctrl))
        status_cnt_en = 1'b1;
      else if (crc_cnt_end && curr_cmd_go && acc_type_write)
        status_cnt_en = 1'b1;
      else if (data_cnt_end && curr_cmd_go && acc_type_read)
        status_cnt_en = 1'b1;
      else if (addr_len_cnt_end && (curr_cmd_rd_comm || curr_cmd_rd_ctrl))
        status_cnt_en = 1'b1;
      else
        status_cnt_en = 1'b0;
    end
  else
    status_cnt_en = 1'b0;
end


assign status_cnt_end = status_cnt == `DBG_CPU_STATUS_LEN;


// Latching acc_type, address and length
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      acc_type  <=  {`DBG_CPU_ACC_TYPE_LEN{1'b0}};
      adr       <=  {`DBG_CPU_ADR_LEN{1'b0}};
      len       <=  {`DBG_CPU_LEN_LEN{1'b0}};
      set_addr  <=  1'b0;
    end
  else if(crc_cnt_end && (!crc_cnt_end_q) && crc_match_i && curr_cmd_wr_comm)
    begin
      acc_type  <=  dr[`DBG_CPU_ACC_TYPE_LEN + `DBG_CPU_ADR_LEN + `DBG_CPU_LEN_LEN -1 : `DBG_CPU_ADR_LEN + `DBG_CPU_LEN_LEN];
      adr       <=  dr[`DBG_CPU_ADR_LEN + `DBG_CPU_LEN_LEN -1 : `DBG_CPU_LEN_LEN];
      len       <=  dr[`DBG_CPU_LEN_LEN -1:0];
      set_addr  <=  1'b1;
    end
  else if(cpu_end_tck)               // Writing back the address
    begin
      adr  <=  cpu_addr_dsff;
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
    len_var <=  {1'b0, {`DBG_CPU_LEN_LEN{1'b0}}};
  else if(update_dr_i)
    len_var <=  len + 'd1;
  else if (start_rd_tck)
    begin
      if (len_var > 4)
        len_var <=  len_var - 'd4; 
      else
        len_var <=  {1'b0, {`DBG_CPU_LEN_LEN{1'b0}}};
    end
end


assign len_eq_0 = len_var == 'h0;


assign half = data_cnt[3:0] == 4'd15;
assign long = data_cnt[4:0] == 5'd31;


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      half_q <=   1'b0;
      long_q <=   1'b0;
    end
  else
    begin
      half_q <=  half;
      long_q <=  long;
    end
end


// Start cpu write cycle
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      start_wr_tck <=  1'b0;
      cpu_dat_tmp <=  32'd0;
    end
  else if (curr_cmd_go && acc_type_write)
    begin
      if (long_q)
        begin
          start_wr_tck <=  1'b1;
          cpu_dat_tmp <=  dr[31:0];
        end
      else
        begin
          start_wr_tck <=  1'b0;
        end
    end
  else
    start_wr_tck <=  1'b0;
end


// cpu_data_o in WB clk domain
always @ (posedge cpu_clk_i)
begin
  cpu_data_dsff <=  cpu_dat_tmp;
end

assign cpu_data_o = cpu_data_dsff;


// Start cpu read cycle
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    start_rd_tck <=  1'b0;
  else if (curr_cmd_go && (!curr_cmd_go_q) && acc_type_read)              // First read after cmd is entered
    start_rd_tck <=  1'b1;
  else if ((!start_rd_tck) && curr_cmd_go && acc_type_read  && (!len_eq_0) && (!fifo_full) && (!rd_tck_started) && (!cpu_ack_tck))
    start_rd_tck <=  1'b1;
  else
    start_rd_tck <=  1'b0;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    rd_tck_started <=  1'b0;
  else if (update_dr_i || cpu_end_tck && (!cpu_end_tck_q))
    rd_tck_started <=  1'b0;
  else if (start_rd_tck)
    rd_tck_started <=  1'b1;
end



always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      start_rd_csff   <=  1'b0;
      start_cpu_rd    <=  1'b0;
      start_cpu_rd_q  <=  1'b0;

      start_wr_csff   <=  1'b0;
      start_cpu_wr    <=  1'b0;
      start_cpu_wr_q  <=  1'b0;

      set_addr_csff   <=  1'b0;
      set_addr_cpu    <=  1'b0;
      set_addr_cpu_q  <=  1'b0;

      cpu_ack_q       <=  1'b0;
    end
  else
    begin
      start_rd_csff   <=  start_rd_tck;
      start_cpu_rd    <=  start_rd_csff;
      start_cpu_rd_q  <=  start_cpu_rd;

      start_wr_csff   <=  start_wr_tck;
      start_cpu_wr    <=  start_wr_csff;
      start_cpu_wr_q  <=  start_cpu_wr;

      set_addr_csff   <=  set_addr;
      set_addr_cpu    <=  set_addr_csff;
      set_addr_cpu_q  <=  set_addr_cpu;

      cpu_ack_q       <=  cpu_ack_i;
    end
end


// cpu_stb_o
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    cpu_stb_o <=  1'b0;
  else if (cpu_ack_i)
    cpu_stb_o <=  1'b0;
  else if ((start_cpu_wr && (!start_cpu_wr_q)) || (start_cpu_rd && (!start_cpu_rd_q)))
    cpu_stb_o <=  1'b1;
end


assign cpu_stall_o = cpu_stb_o | cpu_reg_stall;
                                                                                

// cpu_addr_o logic
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    cpu_addr_dsff <=  32'h0;
  else if (set_addr_cpu && (!set_addr_cpu_q)) // Setting starting address
    cpu_addr_dsff <=  adr;
  else if (cpu_ack_i && (!cpu_ack_q))
    //cpu_addr_dsff <=  cpu_addr_dsff + 3'd4;
    // Increment by just 1, to allow block reading -- jb 090901
    cpu_addr_dsff <=  cpu_addr_dsff + 'd1;
end


assign cpu_addr_o = cpu_addr_dsff;


always @ (posedge cpu_clk_i)
begin
  cpu_we_dsff <=  curr_cmd_go && acc_type_write;
end


assign cpu_we_o = cpu_we_dsff;



// Logic for detecting end of transaction
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    cpu_end <=  1'b0;
  else if (cpu_ack_i && (!cpu_ack_q))
    cpu_end <=  1'b1;
  else if (cpu_end_rst)
    cpu_end <=  1'b0;
end
                                                                                               
                                                                                               
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      cpu_end_csff  <=  1'b0;
      cpu_end_tck   <=  1'b0;
      cpu_end_tck_q <=  1'b0;
    end
  else
    begin
      cpu_end_csff  <=  cpu_end;
      cpu_end_tck   <=  cpu_end_csff;
      cpu_end_tck_q <=  cpu_end_tck;
    end
end


always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      cpu_end_rst_csff <=  1'b0;
      cpu_end_rst      <=  1'b0;
    end
  else
    begin
      cpu_end_rst_csff <=  cpu_end_tck;
      cpu_end_rst      <=  cpu_end_rst_csff;
    end
end


always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    busy_cpu <=  1'b0;
  else if (cpu_end_rst)
    busy_cpu <=  1'b0;
  else if (cpu_stb_o)
    busy_cpu <=  1'b1;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      busy_csff       <=  1'b0;
      busy_tck        <=  1'b0;

      update_dr_csff  <=  1'b0;
      update_dr_cpu   <=  1'b0;
    end
  else
    begin
      busy_csff       <=  busy_cpu;
      busy_tck        <=  busy_csff;

      update_dr_csff  <=  update_dr_i;
      update_dr_cpu   <=  update_dr_csff;
    end
end


// Detecting overrun when write operation.
always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    cpu_overrun <=  1'b0;
  else if(start_cpu_wr && (!start_cpu_wr_q) && cpu_ack_i)
    cpu_overrun <=  1'b1;
  else if(update_dr_cpu) // error remains active until update_dr arrives
    cpu_overrun <=  1'b0;
end


// Detecting underrun when read operation
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    underrun_tck <=  1'b0;
  else if(latch_data && (!fifo_full) && (!data_cnt_end))
    underrun_tck <=  1'b1;
  else if(update_dr_i) // error remains active until update_dr arrives
    underrun_tck <=  1'b0;
end


always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    begin
      cpu_overrun_csff <=  1'b0;
      cpu_overrun_tck  <=  1'b0;

      cpu_ack_csff     <=  1'b0;
      cpu_ack_tck      <=  1'b0;
    end
  else
    begin
      cpu_overrun_csff <=  cpu_overrun;
      cpu_overrun_tck  <=  cpu_overrun_csff;

      cpu_ack_csff     <=  cpu_ack_i;
      cpu_ack_tck      <=  cpu_ack_csff;
    end
end



always @ (posedge cpu_clk_i or posedge rst_i)
begin
  if (rst_i)
    begin
      cpu_ce_csff  <=  1'b0;
      mem_ptr_init      <=  1'b0;
    end
  else
    begin
      cpu_ce_csff  <=   cpu_ce_i;
      mem_ptr_init      <=  ~cpu_ce_csff;
    end
end


// Logic for latching data that is read from cpu
always @ (posedge cpu_clk_i)
begin
  if (cpu_ack_i && (!cpu_ack_q))
    begin
      mem[0] <=  cpu_data_i[31:24];
      mem[1] <=  cpu_data_i[23:16];
      mem[2] <=  cpu_data_i[15:08];
      mem[3] <=  cpu_data_i[07:00];
    end
end


assign input_data = {mem[0], mem[1], mem[2], mem[3]};


// Fifo counter and empty/full detection
always @ (posedge tck_i or posedge rst_i)
begin
  if (rst_i)
    fifo_full <=  1'h0;
  else if (update_dr_i)
    fifo_full <=  1'h0;
  else if (cpu_end_tck && (!cpu_end_tck_q) && (!latch_data) && (!fifo_full))  // incrementing
    fifo_full <=  1'b1;
  else if (!(cpu_end_tck && (!cpu_end_tck_q)) && latch_data && (fifo_full))  // decrementing
    fifo_full <=  1'h0;
end



// TDO multiplexer
always @ (pause_dr_i or busy_tck or crc_cnt_end or crc_cnt_end_q or curr_cmd_wr_comm or curr_cmd_wr_ctrl or curr_cmd_go or acc_type_write or acc_type_read or crc_match_i or data_cnt_end or dr or data_cnt_end_q or crc_match_reg or status_cnt_en or status or addr_len_cnt_end or addr_len_cnt_end_q or curr_cmd_rd_comm or curr_cmd_rd_ctrl)
begin
  if (pause_dr_i)
    begin
    tdo_o = busy_tck;
    end
  else if (crc_cnt_end && (!crc_cnt_end_q) && (curr_cmd_wr_comm || curr_cmd_wr_ctrl || curr_cmd_go && acc_type_write ))
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
  else if ((curr_cmd_rd_comm || curr_cmd_rd_ctrl) && addr_len_cnt_end && (!addr_len_cnt_end_q))
    begin
      tdo_o = ~crc_match_reg;
    end
  else if ((curr_cmd_rd_comm || curr_cmd_rd_ctrl) && crc_cnt_end && (!addr_len_cnt_end))
    begin
      tdo_o = dr[`DBG_CPU_ACC_TYPE_LEN + `DBG_CPU_ADR_LEN + `DBG_CPU_LEN_LEN -1];
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
    status <=  {`DBG_CPU_STATUS_LEN{1'b0}};
    end
  else if(crc_cnt_end && (!crc_cnt_end_q) && (!(curr_cmd_go && acc_type_read)))
    begin
    status <=  {1'b0, 1'b0, cpu_overrun_tck, crc_match_i};
    end
  else if (data_cnt_end && (!data_cnt_end_q) && curr_cmd_go && acc_type_read)
    begin
    status <=  {1'b0, 1'b0, underrun_tck, crc_match_reg};
    end
  else if (addr_len_cnt_end && (!addr_len_cnt_end) && (curr_cmd_rd_comm || curr_cmd_rd_ctrl))
    begin
    status <=  {1'b0, 1'b0, 1'b0, crc_match_reg};
    end
  else if (shift_dr_i && (!status_cnt_end))
    begin
    status <=  {status[`DBG_CPU_STATUS_LEN -2:0], status[`DBG_CPU_STATUS_LEN -1]};
    end
end
// Following status is shifted out (MSB first):
// 3. bit:          1 if crc is OK, else 0
// 2. bit:          1'b0
// 1. bit:          0
// 0. bit:          1 if overrun occured during write (data couldn't be written fast enough)
//                    or underrun occured during read (data couldn't be read fast enough)



// Connecting cpu registers
assign cpu_reg_we = crc_cnt_end && (!crc_cnt_end_q) && crc_match_i && curr_cmd_wr_ctrl;
assign cpu_reg_data_i = dr[`DBG_CPU_DR_LEN -1:`DBG_CPU_DR_LEN -`DBG_CPU_CTRL_LEN];

dbg_cpu_registers i_dbg_cpu_registers 
  (
    .data_i          (cpu_reg_data_i), 
    .we_i            (cpu_reg_we),
    .tck_i           (tck_i),
    .bp_i            (cpu_bp_i),
    .rst_i           (rst_i),
    .cpu_clk_i       (cpu_clk_i),
    .ctrl_reg_o      (ctrl_reg),
    .cpu_stall_o     (cpu_reg_stall),
    .cpu_rst_o       (cpu_rst_o)
  );





endmodule

