from io import StringIO

from pdp8.reggies import *



class Texts(Term):
    def __init__(self, *texts):
        self.texts = texts

    def expr(self):
        return '(%s)' % '|'.join(self.texts)


def texts(*texts):
    return Texts(*texts)

g1values = {
# Mnemonic  Octal   Operation                         Sequence
'NOP':      0o7000, # No operation                         -
'CLA':      0o7200, # Clear AC                             1
'CLL':      0o7100, # Clear link bit                       1
'СМА':      0o7040, # Complement AC                        2
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

g3values = {

}
"""
"""

comma = text(',')
star = text('*')
label = (optional(identifier + comma + space).called('label'))
offset = (space + (digits | identifier).called('offset'))
i = (osp + optional(text('I').called('I')))
z = (osp + optional(text('Z').called('Z')))
mri = texts('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP').called('mri')
g1 =  multiple(osp+texts('NOP', 'CLA', 'CLL', 'СМА', 'CML', 'RAR', 'RAL', 'RTR', 'RTL', 'IAC')).called('group1')
g2 =  multiple(osp+texts('CLA', 'HLT', 'OSR', 'SKP', 'SMA', 'SNA', 'SNL', 'SPA', 'SZA', 'SZL')).called('group2')
opr = (g1 | g2).called('opr')
org = (star + digits.called('org'))


class Parser:
    def __init__(self):
        self.statements = [
            label + mri + i + z + offset,
            label + opr,
            org
        ]
    def parse(self, input):
        for line in input:
            self.parse_line(line.strip())

    def match(self, line, statement):
        m = statement.matches(line)
        if m:
            return self.values(m, statement)
        return None

    def parse_line(self, line):
        if not line:
            return
        for statement in self.statements:
            m = self.match(line, statement)
            if m:
                self.plant(m)
    def plant(self, parsed):
        if parsed:
            print(parsed)
        return parsed

    def values(self, match, term):
        result = {}
        names = term.names()
        for fname in names:
            value = self.field(fname, match)
            if value:
                result[fname] = value
        return result

    def field(self, fname, match):
        if not match:
            return None
        return match.group(fname)

prog = """
*200
AND 7
FOO, AND I Z 73
*700
NOP
CLA CLL
"""

f = StringIO(prog)
Parser().parse(f)


