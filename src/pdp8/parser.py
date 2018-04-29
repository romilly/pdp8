from pdp8.reggies import *

comma = text(',')
label = g('label', identifier + comma + space)


class Texts(Term):
    def __init__(self, *texts):
        self.texts = texts

    def expr(self):
        return '(%s)' % '|'.join(self.texts)


def texts(*texts):
    return Texts(*texts)


offset = g('offset', space + digits | identifier)
i = g('I', osp + optional(text('I')))
z = g('Z', osp + optional(text('Z')))
mri = g('mri', texts('AND', 'TAD', 'ISZ', 'DCA', 'JMS', 'JMP'))


class Parser:
    def mri(self, line):
        syntax = optional(label) + mri + i + z +  offset
        self.match = syntax.matches(line)
        if self.match:
            return self.values()
        return None

    def values(self):
        result = {}
        for f in ['label','mri','I','Z','offset']:
            value = self.field(f)
            if value:
                result[f] = value
        return result

    def field(self, name):
        if not self.match:
            return None
        return self.match.group(name)


print(Parser().mri('AND 7'))
print(Parser().mri('FOO, AND I Z 7'))


