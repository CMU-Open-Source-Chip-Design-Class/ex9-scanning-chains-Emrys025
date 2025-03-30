TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(shell pwd)/fault/fault2.sv
TOPLEVEL = fault
MODULE = ScanChain_starter
SIM = verilator
EXTRA_ARGS += --trace -Wno-WIDTHTRUNC -Wno-UNOPTFLAT -Wno-fatal
include $(shell cocotb-config --makefiles)/Makefile.sim
