from abc import ABCMeta, abstractmethod

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
