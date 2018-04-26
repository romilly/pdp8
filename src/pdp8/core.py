# coding: utf-8
from collections import OrderedDict
from io import StringIO


class PDP8:
    W_BITS = 12                 # number of bits in a word
    W_MASK = 2 ** W_BITS - 1    # word mask
    OP_BITS = 3                 # 3 bits in the opcode
    V_BITS = 7                  # 7 bits for the value part of an instruction
    OP_MASK = (2 ** OP_BITS - 1) << W_BITS - OP_BITS
    V_MASK = 2 ** V_BITS - 1    # mask for instruction data
    MAX = 2 ** (V_BITS - 1)

    def __init__(self):
        self.mem = 2**self.W_BITS*[0]
        self.pc = 0
        self.accumulator = 0
        self.link = 0
        self.running = False
        self.debugging = False
        self.ops = self.setup_ops()
        self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])

    def setup_ops(self):
        ops = OrderedDict()
        ops['NOP'] = self.nop
        # ops['LDC'] = self.ldc
        # ops['ADC'] = self.adc
        # ops['SBC'] = self.sbc
        # ops['STA'] = self.sta
        # ops['LDA'] = self.lda
        # ops['IPA'] = self.ipa
        # ops['OPA'] = self.opa
        ops['HALT'] = self.halt
        return ops

    def __getitem__(self, address):
        return self.mem[address]

    def __setitem__(self, address, contents):
        self.mem[address] = contents & self.W_MASK # only 12 bits stored

    def run(self, debugging=False, start=0, tape=''):
        self.running = True
        self.pc = start
        self.tape = StringIO(tape)
        self.debugging = debugging
        while self.running:
            instruction = self[self.pc]
            self.execute(instruction)

    def execute(self, instruction):
        if self.debugging:
            print('PC: %d (PC) %5d  %4s %5d Accumulator: %5d' %
                  (self.pc, instruction,
                   self.mnemonic_for(instruction),
                   instruction & self.V_MASK,
                   self.accumulator))
        op = self.opcode(instruction)
        self.pc += 1
        self.fns[op](instruction)

    def mnemonic_for(self, instruction):
        code = self.opcode(instruction)
        return self.mnemonics[code] if code < len(self.mnemonics) else '**'

    def opcode(self, instruction):
        bits = instruction & self.OP_MASK
        code = bits >> self.W_BITS - self.OP_BITS
        return code

    def nop(self, instruction):
        pass

    def halt(self, instruction):
        if self.debugging:
            print('Halted')
        self.running = False
    
cpu = PDP8()
cpu[0] = 0 # NOP
cpu[1] = 1 << 9 # HALT
cpu.run(debugging=True)

