`include "wb_bfm_params.v"
function get_cycle_type;
   input [2:0] cti;
   begin
      get_cycle_type = (cti === 3'b000) ? CLASSIC_CYCLE : BURST_CYCLE;
   end
endfunction //

   function is_last;
      input [2:0] 	   cti;
      begin
	 case (cti)
	   3'b000 : begin
	      is_last = 1'b1;
	   end
	   3'b001 : begin
	      is_last = 1'b0;
	   end
	   3'b010 : begin
	      is_last = 1'b0;
	   end
	   3'b111 : begin
	      is_last = 1'b1;
	   end
	   default : $error("%d : Illegal Wishbone B3 cycle type (%b)", $time, cti);
	 endcase // case (wb_cti_i)
      end
   endfunction

function [aw-1:0] next_addr;
   input [aw-1:0] addr_i;
   input [2:0] burst_type_i;
   begin
      case (burst_type_i)
	LINEAR_BURST   : next_addr = addr_i + 4;
	WRAP_4_BURST   : next_addr = {addr_i[aw-1:4], addr_i[3:0]+4'd4};
	WRAP_8_BURST   : next_addr = {addr_i[aw-1:5], addr_i[4:0]+5'd4};
	WRAP_16_BURST  : next_addr = {addr_i[aw-1:6], addr_i[5:0]+6'd4};
	CONSTANT_BURST : next_addr = addr_i;
	default : $error("%d : Illegal burst type (%b)", $time, burst_type_i);
      endcase // case (burst_type_i)
   end
endfunction

