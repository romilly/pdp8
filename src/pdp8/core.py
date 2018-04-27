# coding: utf-8
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from io import StringIO


class Tracer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        pass

    @abstractmethod
    def setting(self, address, contents):
        pass


class NullTracer(Tracer):
    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        pass

    def setting(self, address, contents):
        pass


class PrintingTracer(Tracer):
    def setting(self, address, contents):
        print('setting %5d to %5d' % (address, contents))

    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        print('PC(before): %5d Opcode: %-4s Accumulator: %5d Link: %d PC(after): %5d' %
              (old_pc, opcode, accumulator, link, new_pc))

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
        self.ops = self.setup_ops()
        self.mnemonics = list([mnemonic for mnemonic in self.ops.keys()])
        self.fns = list([self.ops[mnemonic] for mnemonic in self.mnemonics])
        if tracer is None:
            tracer = NullTracer()
        self.tracer = tracer

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
        return self.mem[address] & self.W_MASK # only 12 bits retrieved

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
        self.fns[op](instruction)
        if self.debugging:
            self.tracer.instruction(old_pc, self.mnemonic_for(instruction), self.accumulator, self.link, self.pc)

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


