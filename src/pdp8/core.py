from io import StringIO
from pdp8.tracing import NullTracer



def octal(string):
    return int(string, 8)

OPR_GROUP1 = octal('0400')
OPR_GROUP2 = octal('0001')
CLA1 = octal('0200')
CLL = octal('0100')
CMA = octal('0040')
CML = octal('0020')
RAR = octal('0010')
RAL = octal('0004')
RTR = octal('0012')
RTL = octal('0006')
IAC = octal('0001')
HALT = octal('0002')
BIT8 = octal('0010')
Z_BIT = 0o0200
I_BIT = 0o0400

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
        # self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        # self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])
        if tracer is None:
            tracer = NullTracer()
        self.tracer = tracer
        self.ops =  [PDP8.andi,
                PDP8.tad,
                PDP8.isz,
                PDP8.dca,
                PDP8.jms,
                PDP8.jmp,
                PDP8.iot,
                PDP8.opr]

    def __getitem__(self, address):
        return self.memory[address] & self.W_MASK # only 12 bits retrieved

    def is_group1(self):
        return 0 == self.i_mask(OPR_GROUP1)

    def i_mask(self, mask):
        return self.instruction & mask

    def is_iac(self):
        return 0 != self.i_mask(IAC)

    def is_group2(self):
        return (not self.is_group1()) and 0 == self.i_mask(OPR_GROUP2)

    # Group 2
    def is_halt(self):
        return self.i_mask(HALT)

    def is_or_group(self):
        return not self.i_mask(BIT8)

    def i_bit(self):
        return self.i_mask(I_BIT)

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
            self.instruction = self[self.pc]
            self.execute()

    def execute(self):
        old_pc = self.pc # for debugging
        op = self.opcode()
        self.pc += 1
        self.ops[op](self)
        # if self.debugging:
        #     self.tracer.instruction(old_pc, self.mnemonic_for(instruction), self.accumulator, self.link, self.pc)
        if self.stepping:
            self.running = False

    def opcode(self):
        bits = self.i_mask(self.OP_MASK)
        code = bits >> self.W_BITS - self.OP_BITS
        return code

    def andi(self):
        self.accumulator &= self[self.instruction_address()]

    # TODO: set carry bit
    def tad(self):
        self.add_12_bits(self[self.instruction_address()])

    def add_12_bits(self, increment):
        self.accumulator += increment
        total = self.accumulator
        self.accumulator &= octal('7777')
        if self.accumulator == total:
            self.link = 0
        else:
            self.link = 1

    def isz(self):
        address = self.instruction_address()
        contents = self[address]
        contents += 1
        self[address] = contents # forces 12-bit value
        if self[address] == 0:
            self.pc += 1 # skip

    def dca(self):
        self[self.instruction_address()] = self.accumulator
        self.accumulator = 0

    def jmp(self):
        self.pc = self.instruction_address()

    def jms(self):
        self[self.instruction_address()] = self.pc
        self.pc = self.instruction_address() + 1

    # TODO: handle variants
    def iot(self):
        return self.tape.read(1)

    def opr(self):
        if  self.is_group1():
            self.group1()
        if self.is_group2():
            self.group2()

    def instruction_address(self):
        o = self.i_mask(self.V_MASK)
        if not self.i_mask(Z_BIT):
            o += self.pc & 0o7600
        if self.i_mask(I_BIT):
            o = self[o]
        return o

    def cla(self):
        self.accumulator = 0

    def cll(self):
        self.link = 0

    def cma(self):
        self.accumulator ^= 0o7777

    def cml(self):
        self.link = 1-self.link

    def rr(self):
        self.rar(0 < self.i_mask(2))

    def rar(self, flag):
        count = 2 if flag else 1
        for i in range(count):
            new_link = self.accumulator & 0o0001
            self.accumulator = self.accumulator >> 1
            if self.link:
                self.accumulator |= 0o4000
            self.link = new_link

    def rl(self):
        self.ral(self.i_mask(2))

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

    def group1(self):
        for (mask, ins) in zip([     CLA1,     CLL,      CMA,      CML,      IAC,     RAR,     RAL],
                               [self.cla, self.cll, self.cma, self.cml, self.iac,self.rr, self.rl]):
            if self.i_mask(mask):
                ins()

    def group2(self):
        if self.is_or_group():
            if self.sma() or self.sza() or self.snl():
                self.pc += 1
        if self.is_halt():
            self.halt()

    def sma(self):
        return self.accumulator & octal('4000') and (self.i_mask(octal('0100')))

    def sza(self):
        return False

    def snl(selfn):
        return False





