from io import StringIO

from pdp8.core import PDP8, PrintingTracer
from tests.helpers.checker import ConfigChecker


class Assembler():
    def __init__(self, pdp8):
        self.pdp8 = pdp8
        self.ops = pdp8.instruction_set.ops
        self.origin = 0

    def org(self, address):
        self.origin = address

    def plant(self, instruction):
        self.pdp8[self.origin] = instruction
        self.origin += 1

    def compile(self, prog):
        p = StringIO(prog)
        for line in p:
            if len(line.strip()) > 0:
                self.parse(line)

    def parse(self, line):
        parts = line.strip().split(' ')
        opcode = parts[0].strip()
        v = 0
        if opcode in self.ops:
            op = list(self.ops.keys()).index(opcode)
        else:
            raise ValueError('Invalid opcode in %s' % line)
        if len(parts) == 2:
            v = int(parts[1].strip())
        if len(parts) > 2:
            raise ValueError('Invalid format: %s' % line)
        self.plant(self.ins(op, v))

    def ins(self, op, value=0):
        instruction = (value & self.pdp8.V_MASK) | (op << self.pdp8.W_BITS - self.pdp8.OP_BITS)
        return instruction


if __name__ == '__main__':
    pdp8 = PDP8(tracer=PrintingTracer())
    asm = Assembler(pdp8)
    asm.org(100)
    asm.compile("""
        NOP
        HALT
        """)
    pdp8.run(start=100, debugging=True)
    ConfigChecker(pdp8).check(memory=[(0, 0)])
    ConfigChecker(pdp8).check(pc=102)