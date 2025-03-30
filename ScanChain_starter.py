import copy
import cocotb
from cocotb.triggers import Timer


# Make sure to set FILE_NAME
# to the filepath of the .log
# file you are working with
CHAIN_LENGTH = 13
FILE_NAME    = "adder/adder.log"



# Holds information about a register
# in your design.

################
# DO NOT EDIT!!!
################
class Register:

    def __init__(self, name) -> None:
        self.name = name            # Name of register, as in .log file
        self.size = -1              # Number of bits in register

        self.bit_list = list()      # Set this to the register's contents, if you want to
        self.index_list = list()    # List of bit mappings into chain. See handout

        self.first = -1             # LSB mapping into scan chain
        self.last  = -1             # MSB mapping into scan chain


# Holds information about the scan chain
# in your design.
        
################
# DO NOT EDIT!!!
################
class ScanChain:

    def __init__(self) -> None:
        self.registers = dict()     # Dictionary of Register objects, indexed by 
                                    # register name
        
        self.chain_length = 0       # Number of FFs in chain


# Sets up a new ScanChain object
# and returns it

################     
# DO NOT EDIT!!!
################
def setup_chain(filename):

    scan_chain = ScanChain()

    f = open(filename, "r")
    for line in f:
        linelist = line.split()
        index, name, bit = linelist[0], linelist[1], linelist[2]

        if name not in scan_chain.registers:
            reg = Register(name)
            reg.index_list.append((int(bit), int(index)))
            scan_chain.registers[name] = reg

        else:
            scan_chain.registers[name].index_list.append((int(bit), int(index)))
        
    f.close()

    for name in scan_chain.registers:
        cur_reg = scan_chain.registers[name]
        cur_reg.index_list.sort()
        new_list = list()
        for tuple in cur_reg.index_list:
            new_list.append(tuple[1])
        
        cur_reg.index_list = new_list
        cur_reg.bit_list   = [0] * len(new_list)
        cur_reg.size = len(new_list)
        cur_reg.first = new_list[0]
        cur_reg.last  = new_list[-1]
        scan_chain.chain_length += len(cur_reg.index_list)

    return scan_chain


# Prints info of given Register object

################
# DO NOT EDIT!!!
################
def print_register(reg):
    print("------------------")
    print(f"NAME:    {reg.name}")
    print(f"BITS:    {reg.bit_list}")
    print(f"INDICES: {reg.index_list}")
    print("------------------")


# Prints info of given ScanChain object

################   
# DO NOT EDIT!!!
################
def print_chain(chain):
    print("---CHAIN DISPLAY---\n")
    print(f"CHAIN SIZE: {chain.chain_length}\n")
    print("REGISTERS: \n")
    for name in chain.registers:
        cur_reg = chain.registers[name]
        print_register(cur_reg)



#-------------------------------------------------------------------

# This function steps the clock once.
    
# Hint: Use the Timer() builtin function
async def step_clock(dut):

    dut.clk.value = 1
    await Timer(10, units='ns')
    dut.clk.value = 0
    await Timer(10, units='ns')
    

#-------------------------------------------------------------------

# This function places a bit value inside FF of specified index.
        
# Hint: How many clocks would it take for value to reach
#       the specified FF?
        
async def input_chain_single(dut, bit, ff_index):
    # 0 1 2 3 4 5 6 7 8 9 10 11 12
    # 0 0 0 0 1 0 0 0 0 0 0  0  0
    dut.scan_en.value = 1
    for i in range(ff_index + 1):
        if i == 0:
            dut.scan_in.value = bit
        else:
            dut.scan_in.value = 0
        await step_clock(dut)
    dut.scan_en.value = 0
    
#-------------------------------------------------------------------

# This function places multiple bit values inside FFs of specified indexes.
# This is an upgrade of input_chain_single() and should be accomplished
#   for Part H of Task 1
        
# Hint: How many clocks would it take for value to reach
#       the specified FF?
        
async def input_chain(dut, bit_list, ff_index):
    # 0 1 2 3 4 5 6 7 8 9 10 11 12
    # 1 1 1 1 1 0 0 0 0 0 0  0  0
    # 0 0 0 0 1 1 1 1 1 0 0  0  0
    dut.scan_en.value = 1
    reversed_list = bit_list[::-1]
    for bit in reversed_list:
        dut.scan_in.value = bit
        await step_clock(dut)
    for _ in range(ff_index):
        dut.scan_in.value = 0
        await step_clock(dut)
    dut.scan_en.value = 0

#-----------------------------------------------

# This function retrieves a single bit value from the
# chain at specified index 
        
async def output_chain_single(dut, ff_index):

    global CHAIN_LENGTH
    dut.scan_en.value = 1
    num_shifts = CHAIN_LENGTH - ff_index - 1
    for _ in range(num_shifts):
        dut.scan_in.value = 0
        await step_clock(dut)
    value = dut.scan_out.value
    dut.scan_en.value = 0
    return value
    
#-----------------------------------------------

# This function retrieves a single bit value from the
# chain at specified index 
# This is an upgrade of input_chain_single() and should be accomplished
#   for Part H of Task 1
        
async def output_chain(dut, ff_index, output_length):
    # 0 1 2 3 4 5 6 7 8 9 10 11 12
    # 1 1 1 1 1 0 0 0 0 0 0  0  0
    # 0 0 0 0 1 1 1 1 1 0 0  0  0
    global CHAIN_LENGTH
    dut.scan_en.value = 1
    initial_shifts = CHAIN_LENGTH - (ff_index+output_length-1) - 1
    for _ in range(initial_shifts):
        dut.scan_in.value = 0
        await step_clock(dut)
    bits = []
    for _ in range(output_length):
        bits.append(int(dut.scan_out.value))
        dut.scan_in.value = 0
        await step_clock(dut)
    dut.scan_en.value = 0
    return bits  

#-----------------------------------------------

# Your main testbench function

# @cocotb.test()
async def test_adder(dut):

    global CHAIN_LENGTH
    global FILE_NAME        # Make sure to edit this guy
                            # at the top of the file

    # Setup the scan chain object
    chain = setup_chain(FILE_NAME)

    a_val = 0b1011
    b_val = 0b0100
    expected_sum = a_val + b_val  

    # Construct bit_list for the entire scan chain
    bit_list = []
    # bit_list.extend([0] * 5)
    # bit_list.append(0)
    # bit_list.append(1)
    # bit_list.append(0)
    # bit_list.append(1)
    # bit_list.append(0)
    # bit_list.append(1)
    # bit_list.append(1)
    # bit_list.append(0)
    for i in range(4):
        bit_list.append((b_val >> i) & 1)
    for i in range(4):
        bit_list.append((a_val >> i) & 1)

    # Load values into the scan chain
    await input_chain(dut, bit_list, ff_index=5)

    # Disable scan mode and compute the sum
    dut.scan_en.value = 0
    await step_clock(dut)

    # Read x_out from the scan chain
    x_bits = await output_chain(dut, ff_index=0, output_length=5)
    x_bits.reverse()
    x_val = (x_bits[4] << 4) | (x_bits[3] << 3) | (x_bits[2] << 2) | (x_bits[1] << 1) | x_bits[0]

    # Verify the result
    assert x_val == expected_sum, f"Expected {expected_sum} (0b{expected_sum:05b}), got {x_val} (0b{x_val:05b})"
    
    
# @cocotb.test()
async def test_hidden_fsm(dut):
    global CHAIN_LENGTH, FILE_NAME
    FILE_NAME = "hidden_fsm/hidden_fsm.log"
    chain = setup_chain(FILE_NAME)
    CHAIN_LENGTH = 3

    # General Method to identify state register bits from .log file
    state_bit_indices = []
    for name in chain.registers:
        if "state" in name.lower(): 
            state_reg = chain.registers[name]
            state_bit_indices = state_reg.index_list
            break
    state_bit_count = len(state_bit_indices)

    # Test all possible states and inputs
    transitions = []
    for state in range(2**state_bit_count):
        for data_avail in [0, 1]:
            # Initialize scan chain with current state
            bit_list = [0] * CHAIN_LENGTH
            for i, idx in enumerate(state_bit_indices):
                bit_list[idx] = (state >> i) & 1
            await input_chain(dut, bit_list, ff_index=0)

            # Propagate outputs
            dut.scan_en.value = 0
            await Timer(1, units='ns') 
            outputs = {
                'buf_en': dut.buf_en.value,
                'out_sel': dut.out_sel.value,
                'out_writing': dut.out_writing.value
            }

            # Apply input and step clock
            dut.data_avail.value = data_avail
            await step_clock(dut)

            # Read new state
            new_state_bits = []
            new_state_bits = await output_chain(dut, ff_index=0, output_length=state_bit_count)
            new_state = sum(bit << i for i, bit in enumerate(new_state_bits))

            # Prepare for print
            transitions.append({
                'current_state': bin(state),
                'input': data_avail,
                'next_state': bin(new_state),
                'outputs': outputs
            })

    for t in transitions:
        print(f"State: {t['current_state']}, Input: {t['input']} -> Next: {t['next_state']}, Outputs: {t['outputs']}")


@cocotb.test()
async def test_fault_detection(dut):
    test_vectors = [
        ((0, 0, 0, 0), 1),   
        ((1, 0, 0, 0), 0),  
        ((1, 1, 1, 0), 0),
        ((1, 1, 1, 1), 1),
    ]

    fault_map = {
        #a SA1, b SA1, c SA1, e SA0, f SA0, g SA0, h SA0, x SA0 
        0: ["a SA1", "b SA1", "c SA1", "e SA0", "f SA0", "g SA0", "h SA0", "x SA0"],
        # a SA0, b SA1, e SA1, f SA1, x SA1 
        1: ["a SA0", "b SA1", "e SA1", "f SA1", "x SA1"],
        # c SA0, d SA1, g SA1, h SA1, x SA1
        2: ["c SA0", "d SA1", "g SA1", "h SA1", "x SA1"],
        # a SA0, b SA0, d SA0, e SA1, f SA0, h SA0, x SA0
        3: ["a SA0", "b SA0", "d SA0", "e SA1", "f SA0", "h SA0", "x SA0"],
    }

    for idx, (inputs, expected) in enumerate(test_vectors):
        a, b, c, d = inputs
        dut.a.value = a
        dut.b.value = b
        dut.c.value = c
        dut.d.value = d
        await Timer(1, units="ns")
        actual = dut.x.value
        if actual != expected:
            print(f"Fault detected with vector {inputs}: expected {expected}, got {actual}")
            possible_faults = fault_map.get(idx, [])
            print(f"Possible faults: {', '.join(possible_faults)}")
        else:
            print(f"Vector {inputs} passed")

