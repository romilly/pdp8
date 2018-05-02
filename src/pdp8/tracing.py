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


class PrintingTracer(Tracer):
    def setting(self, address, contents):
        print('setting %5d to %5d' % (address, contents))

    def instruction(self, old_pc, opcode, accumulator, link, new_pc):
        print('PC(before): %5d Opcode: %-4s Accumulator: %5d Link: %d PC(after): %5d' %
              (old_pc, opcode, accumulator, link, new_pc))

    def halt(self, pc):
        print('Halted at %d(%o)' % (pc, pc))


class HaltTracer(NullTracer):
    def __init__(self):
        self.halted = False

    def halt(self, pc):
        self.halted = True
