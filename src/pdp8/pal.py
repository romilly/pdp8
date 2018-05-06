from abc import abstractmethod, ABCMeta
from io import StringIO
from operator import add, sub

from pdp8.core import PDP8, octal
from pdp8.tracing import PrintingTracer
from reggie.core import *



# TODO: allow OCTAL, DECIMAL to set base

label = optional(name(identifier,'label') + comma + spaces)
loc = escape('.')
minus = '-'
value1 = one_of(digits, name(identifier, 'id1'), name(loc, 'loc'))
value2 = one_of(digits, name(identifier, 'id2'))
function = name(one_of(plus, minus),'function')
expression = name(value1, 'value1') + optional(osp + function + osp + name(value2,'value2'))
offset = name(expression, 'offset')
i = osp + name(optional('I'),'I')
z = osp + name(optional('Z'),'Z')
mri = name(one_of('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP'),'mri')
g1 =  name(multiple(osp+one_of('NOP', 'CLA', 'CLL', 'CMA', 'CML', 'RAR', 'RAL', 'RTR', 'RTL', 'IAC')),'group1')
g2 =  name(multiple(osp+one_of('CLA', 'HLT', 'OSR', 'SKP', 'SMA', 'SNA', 'SNL', 'SPA', 'SZA', 'SZL')),'group2')
opr = name(one_of(g1, g2),'opr')
org = escape('*') + name(digits,'org')


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
'CMA':      0o7040, # Complement AC                        2
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
'OSR':      0o7404, # Inclusive OR switch register        3
#                    with AC
'HLT':      0o7402, # Halts the program                   3
}


class Parser:
    __metaclass__ = ABCMeta

    def __init__(self, syntax, planter):
        self.syntax = syntax
        self.planter = planter
        self.successor = None
        self.base = 8

    def after(self, successor):
        successor.successor = self
        return successor

    def parse(self, input):
        for line in input:
            line = self.decommented_and_trimmed(line)
            if len(line) > 0:
                self.parse_line(line)

    def match(self, line, statement):
        return match(statement, line)

    def parse_line(self, line):
        statement = self.match(line, self.syntax)
        if statement is None:
            self.pass_the_buck(line)
        else:
            self.plant(statement, line)

    # need to over-ride for org, 'cos it does not generate an instruction
    def plant(self, parsed, line):
        self.planter.plant(self.build_instruction(parsed), line)

    def pass_the_buck(self, line):
        if self.successor is None:
            raise(ValueError('I cannot recognise line %s' % line))
        self.successor.parse_line(line)

    @abstractmethod
    def build_instruction(self, parsed):
        pass

    # remove comment text
    def decommented_and_trimmed(self, line):
        line = line.split('/')[0]
        return line.strip()

    def evaluate_offset(self, parsed):
        op = sub if 'function' in parsed and parsed['function'] == '-' else add
        v1 = self.evaluate_term(1, parsed)
        v2 = self.evaluate_term(2, parsed)
        return op(v1,v2)

    def evaluate_term(self, num, parsed):
        v = 'value%d' % num
        if v not in parsed:
            return 0
        if num == 1 and 'loc' in parsed:
            return self.planter.ic
        t = 'id%d' % num
        if t in parsed:
            return self.planter.symbols[parsed[t]]
        return int(parsed[v], self.base)


class InstructionPlanter():
    def __init__(self):
        self.reset()

    def reset(self):
        self.code = 4096 * [0]
        self.ic = 0
        self.symbols = {}
        self.source = {}

    def plant(self, instruction, line):
        self.code[self.ic] = instruction
        self.source[self.ic] = line
        self.ic += 1

    def org(self, location):
        self.ic = location

    def define(self, symbol):
        self.symbols[symbol] = self.ic

    def evaluate(self, symbol):
        if symbol in self.symbols:
            return self.symbols[symbol]
        raise(ValueError('symbol %s is undefined'))


class MriParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, name(label+mri+i+z+spaces+offset, 'line'), planter)

    def build_instruction(self, parsed):
        op = mri_values[parsed['mri']]
        offset = self.evaluate_offset(parsed)
        if offset < octal('200'):
            parsed['Z'] = 'Z' # force PAGE 0
        offset_page = offset & octal('7400')
        here_page = self.planter.ic & octal('7400')
        if here_page != offset_page:
            raise Exception('%s offset refers to an inaccessible page' % parsed['line'])
        offset = offset & octal('177')
        op |= offset
        if 'Z' in parsed:
            op |= 0o0200
        if 'I' in parsed:
            op |= 0o0400
        return op


class OprParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, label+opr, planter)

    def build_instruction(self, parsed):
        op = 0
        codes = parsed['opr'].split()
        values = g1values if 'group1' in parsed else g2values
        for code in codes:
            code_ = values[code]
            op |= code_
        return op


class Org(Parser):
    def __init__(self, planter):
        Parser.__init__(self, org, planter)

    def plant(self, parsed, line):
        self.planter.org(int(parsed['org'],self.base))

    def build_instruction(self, parsed):
        pass


class ExprParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, label+osp+offset, planter)

    def build_instruction(self, parsed):
        return self.evaluate_offset(parsed)


class LabelParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, label + characters, planter)

    def plant(self, parsed, line):
        if 'label' in parsed:
            self.planter.define(parsed['label'])
        self.planter.plant(0, line)


class ChainBuilder():
    def __init__(self,*parsers):
        self.parsers = parsers

    def build(self):
        for (parser, successor) in zip(self.parsers[:-1],self.parsers[1:]):
            parser.successor = successor
        return self.parsers[0]


class Pal():
    def __init__(self, pdp8):
        self.pdp8 = pdp8
        self.planter = InstructionPlanter()
        self.pass1 = ChainBuilder(Org(self.planter), LabelParser(self.planter)).build()
        self.pass2 = ChainBuilder(MriParser(self.planter),
                                  OprParser(self.planter),
                                  Org(self.planter),
                                  ExprParser(self.planter)
                                  ).build()

    def instruction(self, string):
        self.planter.reset()
        self.pass2.parse_line(string)
        return self.planter.code[0]

    def assemble(self, file_like, list_symbols=False):
        self.planter.reset()
        self.pass1.parse(file_like)
        if list_symbols:
            symbols = self.planter.symbols
            for key in symbols:
                print('%8s = %4d (%4o)' % (key, symbols[key], symbols[key]))
        file_like.seek(0)
        self.planter.ic = 0
        self.pass2.parse(file_like)
        self.pdp8.memory = self.planter.code
        self.pdp8.tracer = PrintingTracer(self.planter.source)
