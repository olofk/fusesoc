ORPSOC_ROOT := $(shell pwd)
-include config/orpsoc.conf
-include config/board.conf
SIM_ROOT   := $(ORPSOC_ROOT)/sim
BOARD_ROOT := $(ORPSOC_ROOT)/boards/$(BOARD)

.phony : config sim
#Configure 
config::
ifeq ("$(wildcard $(BOARD_ROOT)/Makefile)","")
	@echo "Board \"$(BOARD)\" not found"
	@echo "Set BOARD to one of the following boards (e.g. make config BOARD=xilinx-atlys):"
	@echo $(notdir $(wildcard boards/*))
else
	@echo Configuring specific settings for $(BOARD)
	@make -s -C $(BOARD_ROOT) config
	@echo BOARD=$(BOARD) > config/board.conf
endif

sim::
ifeq ("$(wildcard $(SIM_ROOT)/$(SIM)/Makefile)","")
	@echo "ORPSoC doesn't support \"$(SIM)\""
	@echo "The following simulators are supported:"
	@echo $(notdir $(wildcard $(SIM_ROOT)/*))
else

	@make -s -C $(SIM_ROOT)/$(SIM) sim
endif

#Shortcuts for common targets
#############################
sim-modelsim:
	@make -s -C $(SIM_ROOT)/modelsim sim
sim-icarus:
	@make -s -C $(SIM_ROOT)/icarus sim
sim-icarus-wave:
	@make -s -C $(SIM_ROOT)/icarus sim-wave

#Clean targets
##############
clean-config:
	@rm board.conf