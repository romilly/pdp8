from pdp8.reggie import *

comma = text(',')
star = text('*')

label = (optional(identifier.called('label') + comma + space))
offset = (space + (digits | identifier).called('offset'))
i = (osp + optional(text('I').called('I')))
z = (osp + optional(text('Z').called('Z')))
mri = texts('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP').called('mri')
g1 =  multiple(osp+texts('NOP', 'CLA', 'CLL', 'CMA', 'CML', 'RAR', 'RAL', 'RTR', 'RTL', 'IAC')).called('group1')
g2 =  multiple(osp+texts('CLA', 'HLT', 'OSR', 'SKP', 'SMA', 'SNA', 'SNL', 'SPA', 'SZA', 'SZL')).called('group2')
opr = (g1 | g2).called('opr')
org = (star + digits.called('org'))


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
'OSR':      0o7404, # Inclusive OR, switch register       3
#                    with AC
'HLT':      0o7402, # Halts the program                   3
}

opr_values = {**g1values, **g2values} # Yay for Python 3.5!



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
            decommented_and_trimmed = self.strip(line)
            if len(decommented_and_trimmed) > 0:
                self.parse_line(decommented_and_trimmed)

    def match(self, line, statement):
        m = statement.matches(line)
        if m:
            return self.values(m, statement)
        return None

    def parse_line(self, line):
        statement = self.match(line, self.syntax)
        if statement is None:
            self.pass_the_buck(line)
        else:
            self.plant(statement)

    # need to over-ride for org, 'cos it does not generate an instruction
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

    # remove comment text
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
            op |= 0o0400
        if 'Z' in parsed:
            op |= 0o0200
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
            code_ = values[code]
            op |= code_
        return op


class Org(Parser):
    def __init__(self, planter):
        Parser.__init__(self, org, planter)

    def plant(self, parsed):
        self.planter.org(int(parsed['org'],self.base))

    def build_instruction(self, parsed):
        pass


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


if __name__=='__main__':

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


