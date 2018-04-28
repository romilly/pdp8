from pdp8.reggies import *

label = named_group('label', identifier+text(',')+space)


class Texts(Term):
    def __init__(self, *texts):
        self.texts = texts

    def expr(self):
        return '(%s)' % '|'.join(self.texts)


def texts(*texts):
    return Texts(*texts)

offset = named_group('offset', space + digits|identifier)
i = named_group('I', osp + optional(text('I')))
z = named_group('Z', osp + optional(text('Z')))
mri = named_group('mri', texts('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP'))


class Parser:
    def parse(self, line):
        syntax = optional(label) + mri + i + z +  offset
        # syntax = mri + osp + offset
        m = syntax.matches(line)
        return m.group('label'),m.group('mri'),m.group('I'), m.group('Z'), m.group('offset')
        # return m.group('mri'), m.group('offset')

print(Parser().parse('AND 7'))
print(Parser().parse('FOO, AND I Z 7'))


