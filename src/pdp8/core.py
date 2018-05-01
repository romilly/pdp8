from collections import OrderedDict
from io import StringIO

from pdp8.tracing import NullTracer

# TODO: move all mnemonic-based stuff into PAL

"""
(from https://en.wikipedia.org/wiki/PDP-8#Instruction_set)
    000 – AND – AND the memory operand with AC.
    001 – TAD – Two's complement ADd the memory operand to <L,AC> (a 12 bit signed value (AC) w. carry in L).
    010 – ISZ – Increment the memory operand and Skip next instruction if result is Zero.
    011 – DCA – Deposit AC into the memory operand and Clear AC.
    100 – JMS – JuMp to Subroutine (storing return address in first word of subroutine!).
    101 – JMP – JuMP.
    110 – IOT – Input/Output Transfer (see below).
    111 – OPR – microcoded OPeRations (see below). 
"""

mri_values = {
#                Octal     Memory
# Mnemonic(2)    Value     Cycles(1) Instruction
'AND':           0o0000, # 2         Logical AND
'TAD':           0o1000, # 2         Two's Complement Add
'ISZ':           0o2000, # 2         Increment and Skip if Zero
'DCA':           0o3000, # 2         Deposit and Clear the Accumulator
'JMS':           0o4000, # 2         Jump to Subroutine
'JMP':           0o5000, # 1         Jump
}

g1values = {
# Mnemonic  Octal   Operation                         Sequence
'NOP':      0o7000, # No operation                         -
'CLA':      0o7200, # Clear AC                             1
'CLL':      0o7100, # Clear link bit                       1
'СМА':      0o7040, # Complement AC                        2
'CML':      0o7020, # Complement link bit                  2
'RAR':      0o7010, # Rotate AC and L right one position   4
'RAL':      0o7004, # Rotate AC and L left one position    4
'RTR':      0o7012, # Rotate AC and L right two positions  4
'RTL':      0o7006, # Rotate AC and L left two positions   4
'IAC':      0o7001, # Increment AC                         3
}



g2values = {
# Mnemonic  Octal   Operation                           Sequence
'CLA':      0o7600, # Clear the accumulator               2
'SMA':      0o7500, # Skip on minus accumulator           1
'SPA':      0o7510, # Skip on positive accumulator        1
#                    (or AC = 0)
'SZA':      0o7440, # Skip on zero accumulator            1
'SNA':      0o7450, # Skip on nonzero accumulator         1
'SNL':      0o7420, # Skip on nonzero link                1
'SZL':      0o7430, # Skip on zero link                   1
'SKP':      0o7410, # Skip unconditionally                1
'OSR':      0o7404, # Inclusive OR, switch register       3
#                    with AC
'HLT':      0o7402, # Halts the program                   3
}

def octal(string):
    return int(string, 8)

opr_values = {**g1values, **g2values} # Yay for Python 3.5!


class InstructionSet():
    def __init__(self):
        # TODO: separate emulator stuff from PAL stuff
        self.ops = self.setup_ops()
        self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])
        self.OPR_GROUP1 = octal('0400')
        self.CLA1 = octal('0200')
        self.CLL =  octal('0100')

    def setup_ops(self):
        ops = OrderedDict()
        ops['AND'] = PDP8.andi
        ops['TAD'] = PDP8.tad
        ops['ISZ'] = PDP8.isz
        ops['DCA'] = PDP8.dca
        ops['JMS'] = PDP8.jms
        ops['JMP'] = PDP8.jmp
        ops['IOT'] = PDP8.iot
        ops['OPR'] = PDP8.opr
        return ops

    def mnemonic_for(self, instruction):
        code = PDP8.opcode(instruction)
        return self.mnemonics[code] if code < len(self.mnemonics) else '**'

    def is_group1(self, instruction):
        return 0 != instruction & self.OPR_GROUP1

    def has_cla1(self, instruction):
        return 0 != instruction & self.CLA1

    def has_cll(self, instruction):
        return 0 != instruction & self.CLL


class PDP8:
    W_BITS = 12                 # number of bits in a word
    W_MASK = 2 ** W_BITS - 1    # word mask
    OP_BITS = 3                 # 3 bits in the opcode
    V_BITS = 7                  # 7 bits for the value part of an instruction
    OP_MASK = (2 ** OP_BITS - 1) << W_BITS - OP_BITS
    V_MASK = 2 ** V_BITS - 1    # mask for instruction data
    MAX = 2 ** (V_BITS - 1)

    def __init__(self, tracer=None):
        self.memory = 2 ** self.W_BITS * [0]
        self.pc = 0
        self.accumulator = 0
        self.link = 0
        self.running = False
        self.debugging = False
        self.stepping = False
        self.ins = InstructionSet()
        if tracer is None:
            tracer = NullTracer()
        self.tracer = tracer

    def __getitem__(self, address):
        return self.memory[address] & self.W_MASK # only 12 bits retrieved

    # TODO: check and write tests for Z and I
    def z_bit(self, instruction):
        return 0 < instruction & 0o0200

    def i_bit(self, instruction):
        return 0 < instruction & 0o0400

    def __setitem__(self, address, contents):
        self.memory[address] = contents & self.W_MASK # only 12 bits stored
        if self.debugging:
            self.tracer.setting(address, contents)

    def run(self, debugging=False, start=None, tape='', stepping=None):
        self.running = True
        if start:
            self.pc = start
        self.tape = StringIO(tape)
        if stepping is not None:
            self.stepping = stepping
        self.debugging = debugging
        while self.running:
            instruction = self[self.pc]
            self.execute(instruction)

    def execute(self, instruction):
        old_pc = self.pc # for debugging
        op = self.opcode(instruction)
        self.pc += 1
        self.ins.fns[op](self, instruction)
        if self.debugging:
            self.tracer.instruction(old_pc, self.mnemonic_for(instruction), self.accumulator, self.link, self.pc)
        if self.stepping:
            self.running = False

    @classmethod
    def opcode(cls, instruction):
        bits = instruction & cls.OP_MASK
        code = bits >> cls.W_BITS - cls.OP_BITS
        return code

    def andi(self, instruction):
        self.accumulator &= self[self.address_for(instruction)]

    # TODO: set carry bit
    def tad(self, instruction):
        self.accumulator += self[self.address_for(instruction)]

    def isz(self, instruction):
        address = self.address_for(instruction)
        contents = self[address]
        contents += 1
        self[address] = contents # forces 12-bit value
        if self[address] == 0:
            self.pc += 1 # skip

    def dca(self, instruction):
        self[self.address_for(instruction)] = self.accumulator
        self.accumulator = 0

    def jmp(self, instruction):
        self.pc = self.address_for(instruction)

    def jms(self, instruction):
        self[self.address_for(instruction)] = self.pc
        self.pc = self.address_for(instruction) + 1

    # TODO: handle variants
    def iot(self, instruction):
        return self.tape.read(1)

    def opr(self, instruction):
        if  self.ins.is_group1(instruction):
            self.group1(instruction)

    def cla(self):
        self.accumulator = 0

    def cll(self):
        self.link = 0

    def nop(self, instruction):
        pass

    # TODO: handle variants
    def halt(self, instruction):
        if self.debugging:
            print('Halted')
        self.running = False

    def mnemonic_for(self, instruction):
        return self.ins.mnemonic_for(instruction)

    def offset(self, instruction):
        return instruction & self.V_MASK

    def address_for(self, instruction):
        o = self.offset(instruction)
        if self.z_bit(instruction):
            o += self.pc & 0o7600
        if self.i_bit(instruction):
            o = self[o]
        return o

    def group1(self, instruction):
        if self.ins.has_cla1(instruction):
            self.cla()


g1ops = {
# 'NOP':      PDP8.nop,
'CLA':      PDP8.cla, # Clear AC                             1
# 'CLL':      0o7100, # Clear link bit                       1
# 'СМА':      0o7040, # Complement AC                        2
# 'CML':      0o7020, # Complement link bit                  2
# 'RAR':      0o7010, # Rotate AC and L right one position   4
# 'RAL':      0o7004, # Rotate AC and L left one position    4
# 'RTR':      0o7012, # Rotate AC and L right two positions  4
# 'RTL':      0o7006, # Rotate AC and L left two positions   4
# 'IAC':      0o7001, # Increment AC                         3
}



