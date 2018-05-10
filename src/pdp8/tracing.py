from abc import ABCMeta, abstractmethod

class Tracer(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        pass

    @abstractmethod
    def setting(self, address, contents):
        pass

    @abstractmethod
    def halt(self, pc):
        pass


class NullTracer(Tracer):
    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        pass

    def setting(self, address, contents):
        pass

    def halt(self, pc):
        pass


def signed(accumulator):
    return accumulator if accumulator >= 0 else 2**16-accumulator


class PrintingTracer(Tracer):
    def __init__(self, source):
        self.source = source
        self.memset = ''

    def setting(self, address, contents):
        self.memset = '%5d (0o%04o)<=%d' % (address, address, contents)

    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        print(' %30s @ %5d  ac: %5d/%-5d (%04o) l: %d PC(after): %5d %s' %
              (self.source[old_pc], old_pc, accumulator, signed(accumulator), accumulator, link, new_pc, self.memset))
        self.memset = ''

    def halt(self, pc):
        print('Halted at %d(%o)' % (pc, pc))


class HaltTracer(NullTracer):
    def __init__(self):
        self.halted = False

    def halt(self, pc):
        self.halted = True
