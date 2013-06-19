`include "timescale.v"

module orpsoc_tb;

   vlog_tb_utils vlog_tb_utils0();

   ////////////////////////////////////////////////////////////////////////
   //
   // ELF program loading
   // 
   ////////////////////////////////////////////////////////////////////////
   integer mem_words;
   integer i;
   reg [31:0] mem_word;
   reg [1023:0] elf_file;

   initial begin
      if($value$plusargs("or1k_elf_load=%s", elf_file)) begin
	 $or1k_elf_load_file(elf_file);
	 
	 mem_words = $or1k_elf_get_size/4;
	 $display("Loading %d words", mem_words);
	 for(i=0; i < mem_words; i = i+1)
	   orpsoc_tb.dut.wb_bfm_memory0.mem[i] = $or1k_elf_read_32(i*4);
      end else
	$display("No ELF file specified");
      
   end

   ////////////////////////////////////////////////////////////////////////
   //
   // OR1200 monitor
   // 
   ////////////////////////////////////////////////////////////////////////
   or1200_monitor i_monitor();
   
   ////////////////////////////////////////////////////////////////////////
   //
   // DUT
   // 
   ////////////////////////////////////////////////////////////////////////
   orpsoc_top dut();

endmodule
