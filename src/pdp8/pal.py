from io import StringIO

from pdp8.core import mri_values, opr_values, PDP8, g1values, g2values
from pdp8.reggie import *
from pdp8.tracing import PrintingTracer

comma = text(',')
star = text('*')

label = (optional(identifier.called('label') + comma + space))
offset = (space + (digits | identifier).called('offset'))
i = (osp + optional(text('I').called('I')))
z = (osp + optional(text('Z').called('Z')))
mri = texts('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP').called('mri')
g1 =  multiple(osp+texts('NOP', 'CLA', 'CLL', 'СМА', 'CML', 'RAR', 'RAL', 'RTR', 'RTL', 'IAC')).called('group1')
g2 =  multiple(osp+texts('CLA', 'HLT', 'OSR', 'SKP', 'SMA', 'SNA', 'SNL', 'SPA', 'SZA', 'SZL')).called('group2')
opr = (g1 | g2).called('opr')
org = (star + digits.called('org'))


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
            self.parse_line(self.strip(line))

    def match(self, line, statement):
        m = statement.matches(line)
        if m:
            return self.values(m, statement)
        return None

    def parse_line(self, line):
        if not line:
            return
        statement = self.match(line, self.syntax)
        if statement is not None:
            self.plant(statement)
        else:
            self.pass_the_buck(line)

    # need to over-ride for org
    def plant(self, parsed):
        self.planter.plant(self.build_instruction(parsed))

    def values(self, match, term):
        result = {}
        names = term.names()
        for fieldname in names:
            value = self.field(fieldname, match)
            if value:
                result[fieldname] = value
        return result

    def field(self, fname, match):
        if not match:
            return None
        return match.group(fname)

    def pass_the_buck(self, line):
        if self.successor is None:
            raise(ValueError('line %s does not match my syntax' % line))
        self.successor.parse_line(line)

    @abstractmethod
    def build_instruction(self, parsed):
        pass

    # remove
    def strip(self, line):
        line = line.split('/')[0]
        return line.strip()


class InstructionPlanter():
    def __init__(self):
        self.reset()

    def reset(self):
        self.code = 4096 * [0]
        self.ic = 0
        self.symbols = {}

    def plant(self, instruction):
        self.code[self.ic] = instruction
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
        Parser.__init__(self, label+mri+i+z+offset, planter)

    def build_instruction(self, parsed):
        op = mri_values[parsed['mri']]
        if 'I' in parsed:
            op |= 0o1000
        if 'Z' in parsed:
            op |= 0o0400
        op |= int(parsed['offset'], self.base)
        return op


class OprParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, label+opr, planter)

    def build_instruction(self, parsed):
        op = 0
        codes = parsed['opr'].split(' ')
        values = g1values if 'group1' in parsed else g2values
        for code in codes:
            op |= values[code]
        return op


class Org(Parser):
    def __init__(self, planter):
        Parser.__init__(self, org, planter)

    def plant(self, parsed):
        self.planter.org(int(parsed['org'],self.base))


class ConstParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, digits.called('digits'), planter)

    def build_instruction(self, parsed):
        return int(parsed['digits'],self.base)


class LabelParser(Parser):
    def __init__(self, planter):
        Parser.__init__(self, label + characters, planter)

    def plant(self, parsed):
        if 'label' in parsed:
            self.planter.define(parsed['label'])
        self.planter.plant(0)


class ChainBuilder():
    def __init__(self,*parsers):
        self.parsers = parsers

    def build(self):
        for (parser, successor) in zip(self.parsers[:-1],self.parsers[1:]):
            parser.successor = successor
        return self.parsers[0]


class Pal():
    def __init__(self):
        self.planter = InstructionPlanter()
        self.pass1 = ChainBuilder(Org(self.planter), LabelParser(self.planter)).build()
        self.pass2 = ChainBuilder(MriParser(self.planter),
                                  OprParser(self.planter),
                                  Org(self.planter),
                                  ConstParser(self.planter)).build()

    def instruction(self, string):
        self.planter.reset()
        self.pass2.parse_line(string)
        return self.planter.code[0]

    def assemble(self, file_like):
        self.planter.reset()
        self.pass1.parse(file_like)
        file_like.seek(0)
        self.planter.ic = 0
        self.pass2.parse(file_like)
        return self.planter.code


prog = """
/ Comment
*200 /start at octal 200
START, CLA
/TAD 0205
/TAD 0206
/DCA 0207
HLT
1537 / constants
2241
0000
"""


pal = Pal()
# f = StringIO(prog)
# code = pal.assemble(f)
# for loc in range(4095):
#     if code[loc] is not 0:
#         print('%d %o' % (loc,code[loc]))
# # for symbol in pal.planter.symbols:
# #     print(symbol, pal.planter.symbols[symbol])
# pdp8 = PDP8(tracer=PrintingTracer())
# pdp8.memory = code
# pdp8.run(debugging=True, start=128, stepping=True)
# pdp8.run()

print('%o' % pal.instruction('CLA CLL'))


