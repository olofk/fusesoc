TARGET           := test_icarus_0
VPI_MODULES      := vpi1.vpi vpi2.vpi
TOPLEVEL         := top_module
IVERILOG_OPTIONS := some iverilog_options
EXTRA_OPTIONS    ?= +plusarg_bool=1 +plusarg_int=42 +plusarg_str=hello

all: $(VPI_MODULES) $(TARGET)

$(TARGET):
	iverilog -s$(TOPLEVEL) -c $(TARGET).scr -o $@ $(IVERILOG_OPTIONS)

run: $(VPI_MODULES) $(TARGET)
	vvp -n -M. -l icarus.log -lxt2 $(patsubst %.vpi,-m%,$(VPI_MODULES)) $(TARGET) $(EXTRA_OPTIONS)

clean:
	$(RM) $(VPI_MODULES) $(TARGET)

vpi1_LIBS := -lsome_lib
vpi1_INCS := -Isrc/vpi_1/
vpi1_SRCS := src/vpi_1/f1 src/vpi_1/f3

vpi1.vpi: $(vpi1_SRCS)
	iverilog-vpi --name=vpi1 $(vpi1_LIBS) $(vpi1_INCS) $?

clean_vpi1:
	$(RM) vpi1.vpi

vpi2_LIBS := 
vpi2_INCS := 
vpi2_SRCS := src/vpi_2/f4

vpi2.vpi: $(vpi2_SRCS)
	iverilog-vpi --name=vpi2 $(vpi2_LIBS) $(vpi2_INCS) $?

clean_vpi2:
	$(RM) vpi2.vpi
