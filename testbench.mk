TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(shell pwd)/hidden_fsm/hidden_fsm.sv
TOPLEVEL = hidden_fsm
MODULE = ScanChain_starter
SIM = verilator
EXTRA_ARGS += --trace -Wno-WIDTHTRUNC -Wno-UNOPTFLAT -Wno-fatal
include $(shell cocotb-config --makefiles)/Makefile.sim
