TARGET           := test_icarus_minimal_0
TOPLEVEL         := top
IVERILOG_OPTIONS := 

all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog -s$(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

run: $(VPI_MODULES) $(TARGET)
	vvp -n -M. -l icarus.log -lxt2 $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(TARGET) $(EXTRA_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)
