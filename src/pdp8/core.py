from collections import OrderedDict
from io import StringIO

from pdp8.tracing import NullTracer

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


class InstructionSet():
    def __init__(self):
        self.ops = self.setup_ops()
        self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])

    def setup_ops(self):
        ops = OrderedDict()
        ops['AND'] = PDP8.andi
        ops['TAD'] = PDP8.tad
        ops['ISZ'] = PDP8.isz
        ops['DCA'] = PDP8.dca
        ops['JMS'] = PDP8.jms
        ops['JMP'] = PDP8.jmp
        ops['IOT'] = PDP8.iot
        # TODO: handle microcodes
        ops['OPR'] = PDP8.opr
        return ops

    def mnemonic_for(self, instruction):
        code = PDP8.opcode(instruction)
        return self.mnemonics[code] if code < len(self.mnemonics) else '**'


class PDP8:
    W_BITS = 12                 # number of bits in a word
    W_MASK = 2 ** W_BITS - 1    # word mask
    OP_BITS = 3                 # 3 bits in the opcode
    V_BITS = 7                  # 7 bits for the value part of an instruction
    OP_MASK = (2 ** OP_BITS - 1) << W_BITS - OP_BITS
    V_MASK = 2 ** V_BITS - 1    # mask for instruction data
    MAX = 2 ** (V_BITS - 1)

    def __init__(self, tracer=None):
        self.mem = 2**self.W_BITS*[0]
        self.pc = 0
        self.accumulator = 0
        self.link = 0
        self.running = False
        self.debugging = False
        self.instruction_set = InstructionSet()
        if tracer is None:
            tracer = NullTracer()
        self.tracer = tracer


    def __getitem__(self, address):
        return self.mem[address] & self.W_MASK # only 12 bits retrieved

    # TODO: check and write tests for Z and I
    def z_bit(self, instruction):
        return 0 < instruction & 0o0200

    def i_bit(self, instruction):
        return 0 < instruction & 0o0400

    def __setitem__(self, address, contents):
        self.mem[address] = contents & self.W_MASK # only 12 bits stored
        if self.debugging:
            self.tracer.setting(address, contents)


    def run(self, debugging=False, start=0, tape=''):
        self.running = True
        self.pc = start
        self.tape = StringIO(tape)
        self.debugging = debugging
        while self.running:
            instruction = self[self.pc]
            self.execute(instruction)

    def execute(self, instruction):
        old_pc = self.pc # for debugging
        op = self.opcode(instruction)
        self.pc += 1
        self.instruction_set.fns[op](self, instruction)
        if self.debugging:
            self.tracer.instruction(old_pc, self.mnemonic_for(instruction), self.accumulator, self.link, self.pc)

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
        self[address] = contents
        if contents == 0:
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

    def nop(self, instruction):
        pass

    # TODO: handle variants
    def opr(self, instruction):
        if self.debugging:
            print('Halted')
        self.running = False

    def mnemonic_for(self, instruction):
        return self.instruction_set.mnemonic_for(instruction)

    def offset(self, instruction):
        return instruction & self.V_MASK

    def address_for(self, instruction):
        o = self.offset(instruction)
        if self.z_bit(instruction):
            o += self.pc & 0o7600
        if self.i_bit(instruction):
            o = self[o]
        return o




