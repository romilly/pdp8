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
Z_BIT = octal('0200')
I_BIT = octal('0400')


class PDP8:
    # TODO simplify these, use constants rather than calculating?
    W_BITS = 12                 # number of bits in a word
    W_MASK = 2 ** W_BITS - 1    # word mask
    OP_BITS = 3                 # 3 bits in the opcode
    V_BITS = 7                  # 7 bits for the value part of an instruction
    OP_MASK = (2 ** OP_BITS - 1) << W_BITS - OP_BITS
    V_MASK = 2 ** V_BITS - 1    # mask for instruction data
    MAX = 2 ** (V_BITS - 1)

    def __init__(self):
        self.memory = 2 ** self.W_BITS * [0]
        self.pc = 0
        self.accumulator = 0
        self.link = 0
        self.running = False
        self.debugging = False
        self.stepping = False
        self.ia = None
        self.instruction = None
        self.tape = StringIO('')
        self.READER1 = 0o03
        self.PUNCH1 = 0o04
        self.punchflag = 0
        self.output = ''
        self.tracer = None
        self.ops = [self.andi,
                    self.tad,
                    self.isz,
                    self.dca,
                    self.jms,
                    self.jmp,
                    self.iot,
                    self.opr]

    def __getitem__(self, address):
        return self.memory[address] & self.W_MASK   # only 12 bits retrieved

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

    def __setitem__(self, address, contents):
        self.memory[address] = contents & self.W_MASK  # only 12 bits stored
        if self.debugging:
            self.tracer.setting(address, contents)

    def run(self, debugging=False, start=None, tape='', stepping=None, tracer=None):
        self.running = True
        if tracer is not None:
                self.tracer = tracer
        else:
            if self.tracer is None:
                self.tracer = NullTracer()
        if start:
            self.pc = start
        # TODO: smarter tape creation to cope with text and binary tapes.
        self.tape = StringIO(tape)
        if stepping is not None:
            self.stepping = stepping
        self.debugging = debugging
        while self.running:
            self.execute()
            if self.stepping:
                self.running = False

    def execute(self):
        old_pc = self.pc  # for debugging
        self.instruction = self[self.pc]
        self.ia = self.instruction_address()
        op = self.opcode()
        self.pc += 1
        self.ops[op]()
        if self.debugging:
            self.tracer.instruction(old_pc, self.instruction, self.accumulator, self.link, self.pc)

    def opcode(self):
        bits = self.i_mask(self.OP_MASK)
        code = bits >> self.W_BITS - self.OP_BITS
        return code

    def andi(self):
        self.accumulator &= self[self.ia]

    def tad(self):
        self.add_12_bits(self[self.ia])

    def add_12_bits(self, increment):
        self.accumulator += increment
        total = self.accumulator
        self.accumulator &= octal('7777')
        if self.accumulator == total:
            self.link = 0
        else:
            self.link = 1

    def isz(self):
        contents = self[self.ia]
        contents += 1
        self[self.ia] = contents  # forces 12-bit value
        if self[self.ia] == 0:
            self.pc += 1  # skip

    def dca(self):
        self[self.ia] = self.accumulator
        self.accumulator = 0

    def jmp(self):
        self.pc = self.ia

    def jms(self):
        self[self.ia] = self.pc
        self.pc = self.ia + 1

    def iot(self):
        device = (self.instruction & 0o0770) >> 3
        io_op = self.instruction & 0o0007
        if device == self.READER1:
            self.reader(io_op)
        elif device == self.PUNCH1:
            self.punch(io_op)
        else:
            raise ValueError('uknown device')

    def opr(self):
        if self.is_group1():
            self.group1()
            return
        if self.is_group2():
            self.group2()
            return
        raise ValueError('Unknown opcode in instruction 0o%o at %d(%o)' % (self.instruction, self.pc-1, self.pc-1) )

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

    def group1(self):
        for (mask, ins) in zip([     CLA1,     CLL,      CMA,      CML,      IAC,     RAR,     RAL],
                               [self.cla, self.cll, self.cma, self.cml, self.iac,self.rr, self.rl]):
            if self.i_mask(mask):
                ins()

    def is_or_group(self):
        return not self.i_mask(BIT8)

    def is_and_group(self):
        return self.i_mask(BIT8)

    def group2(self):
        if self.is_or_group() and (self.sma() or self.sza() or self.snl()):
            self.pc += 1
        if self.is_and_group() and self.spa() and self.sna() and self.szl():
            self.pc += 1
        if self.is_cla2():
            self.cla()
        if self.is_halt():
            self.halt()

    def sma(self):
        return self.accumulator_is_negative() and (self.i_mask(octal('0100')))

    def accumulator_is_negative(self):
        return self.accumulator & octal('4000')

    def sza(self):
        return self.accumulator == 0 and (self.i_mask(octal('0040')))

    def snl(self):
        return self.link == 1 and (self.i_mask(octal('0020')))

    def spa(self):
        return self.accumulator_is_positive() or not (self.i_mask(octal('0100')))

    def accumulator_is_positive(self):
        return not self.accumulator_is_negative()

    def sna(self):
        return self.accumulator != 0 or not (self.i_mask(octal('0040')))

    def szl(self):
        return self.link == 0 or not (self.i_mask(octal('0020')))

    def reader(self, io_op):
        pass

    def punch(self, io_op):
        if (io_op & 1) and self.punchflag:
            self.pc += 1
        if io_op & 2:
            self.punchflag = 0
        if io_op & 4:
            if self.accumulator != 0:
                self.output += str(chr(self.accumulator))
            self.punchflag = 1

    def is_cla2(self):
        return self.instruction & octal('0200')


