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
#
# mri_values = {
# #                Octal     Memory
# # Mnemonic(2)    Value     Cycles(1) Instruction
# 'AND':           0o0000, # 2         Logical AND
# 'TAD':           0o1000, # 2         Two's Complement Add
# 'ISZ':           0o2000, # 2         Increment and Skip if Zero
# 'DCA':           0o3000, # 2         Deposit and Clear the Accumulator
# 'JMS':           0o4000, # 2         Jump to Subroutine
# 'JMP':           0o5000, # 1         Jump
# }

def octal(string):
    return int(string, 8)


class InstructionSet():
    def __init__(self):
        self.setup_ops()
        # self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        # self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])
        self.OPR_GROUP1 = octal('0400')
        self.OPR_GROUP2 = octal('0001')
        self.CLA1 = octal('0200')
        self.CLL =  octal('0100')
        self.CMA =  octal('0040')
        self.CML =  octal('0020')
        self.RAR =  octal('0010')
        self.RAL =  octal('0004')
        self.RTR =  octal('0012')
        self.RTL =  octal('0006')
        self.IAC =  octal('0001')
        self.HALT = octal('0002')
        self.BIT8 = octal('0010')

    def setup_ops(self):
        self.ops =  [PDP8.andi,
                PDP8.tad,
                PDP8.isz,
                PDP8.dca,
                PDP8.jms,
                PDP8.jmp,
                PDP8.iot,
                PDP8.opr]

    # def mnemonic_for(self, instruction):
    #     code = PDP8.opcode(instruction)
    #     return self.mnemonics[code] if code < len(self.mnemonics) else '**'


    def is_group1(self, instruction):
        return 0 == instruction & self.OPR_GROUP1

    # TODO: some refactoring here methinks
    def is_cla1(self, instruction):
        return 0 != instruction & self.CLA1

    def is_cll(self, instruction):
        return 0 != instruction & self.CLL

    def is_cma(self, instruction):
        return 0 != instruction & self.CMA

    def is_cml(self, instruction):
        return 0 != instruction & self.CML

    def is_rr(self, instruction):
        return 0 != instruction & self.RAR

    def is_rl(self, instruction):
        return 0 != instruction & self.RAL

    def is_iac(self, instruction):
        return 0 != instruction & self.IAC

    def is_group2(self, instruction):
        return (not self.is_group1(instruction)) and 0 == instruction & self.OPR_GROUP2


    # Group 2
    def is_halt(self, instruction):
        return 0 != instruction & self.HALT

    def is_or_group(self, instruction):
        return 0 == instruction & self.BIT8


class PDP8:
    # TODO simplify these, use constants rather than calculating?
    # and add I, Z
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
        # TODO: smarter tape creation to cope with text and binary tapes.
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
        self.ins.ops[op](self, instruction)
        # if self.debugging:
        #     self.tracer.instruction(old_pc, self.mnemonic_for(instruction), self.accumulator, self.link, self.pc)
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
        self.add_12_bits(self[self.address_for(instruction)])

    def add_12_bits(self, increment):
        self.accumulator += increment
        total = self.accumulator
        self.accumulator &= octal('7777')
        if self.accumulator == total:
            self.link = 0
        else:
            self.link = 1

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
        if self.ins.is_group2(instruction):
            self.group2(instruction)

    def cla(self):
        self.accumulator = 0

    def cll(self):
        self.link = 0

    def cma(self):
        self.accumulator ^= 0o7777

    def cml(self):
        self.link = 1-self.link

    def rr(self, instruction):
        self.rar(0 < instruction & 2)

    def rar(self, flag):
        count = 2 if flag else 1
        for i in range(count):
            new_link = self.accumulator & 0o0001
            self.accumulator = self.accumulator >> 1
            if self.link:
                self.accumulator |= 0o4000
            self.link = new_link

    def rl(self, instruction):
        self.ral(instruction & 2)

    def ral(self, flag):
        count = 2 if flag else 1
        for i in range(count):
            new_link = 1 if self.accumulator & 0o4000 else 0
            self.accumulator = 0o7777 & self.accumulator << 1
            if self.link:
                self.accumulator |= 0o0001
            self.link = new_link

    def iac(self):
        self.add_12_bits(1)

    def halt(self):
        if self.debugging:
            print('Halted')
        self.tracer.halt(self.pc)
        self.running = False

    # def mnemonic_for(self, instruction):
    #     return self.ins.mnemonic_for(instruction)

    def offset(self, instruction):
        return instruction & self.V_MASK

    def address_for(self, instruction):
        o = self.offset(instruction)
        if not self.z_bit(instruction):
            o += self.pc & 0o7600
        if self.i_bit(instruction):
            o = self[o]
        return o

    def group1(self, instruction):
        # sequence 1
        if self.ins.is_cla1(instruction):
            self.cla()
        if self.ins.is_cll(instruction):
            self.cll()
        # sequence 2
        if self.ins.is_cma(instruction):
            self.cma()
        if self.ins.is_cml(instruction):
            self.cml()
        # sequence 3
        if self.ins.is_iac(instruction):
            self.iac()
        # sequence 4
        if self.ins.is_rr(instruction):
            self.rr(instruction)
        if self.ins.is_rl(instruction):
            self.rl(instruction)

    # TODO: move instructionset stuff back into pdp8 and get rid of all these instruction parameters!
    def group2(self, instruction):
        if self.ins.is_or_group(instruction):
            if self.sma(instruction) or self.sza(instruction) or self.snl(instruction):
                self.pc += 1
        if self.ins.is_halt(instruction):
            self.halt()

    def sma(self, instruction):
        return self.accumulator & octal('4000') and (instruction & octal('0100'))

    def sza(self, instruction):
        return False

    def snl(self, instruction):
        return False





