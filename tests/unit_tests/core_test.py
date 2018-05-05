from abc import ABCMeta
from unittest import TestCase

from hamcrest import assert_that

from pdp8.core import PDP8, octal
from pdp8.pal import Pal
from pdp8.tracing import NullTracer, HaltTracer
from tests.helpers.checker import ConfigChecker

# TODO: Add tests (and then code) for AutoIndexing

class AbstractCodeTest(TestCase):
    __metaclass__ = ABCMeta

    def setUp(self):
        self.pdp = PDP8()
        self.checker = ConfigChecker(self.pdp)
        self.pal = Pal()

    def instruction(self, text):
        return self.pal.instruction(text)

    def check(self, memory=None, pc=None, accumulator=None, link=None):
        self.checker.check(memory, pc, accumulator, link)


class MriTest(AbstractCodeTest):

    def test_and(self):
        self.pdp.accumulator = octal('7070')
        self.pdp.memory[0] = self.instruction('AND 2')
        self.pdp.memory[2] = octal('1120')
        self.pdp.run(stepping=True)
        self.check(accumulator=octal('1020'))

    def test_tad(self):
        self.link = 1
        self.pdp.accumulator = octal('007')
        self.pdp.memory[0] = self.instruction('TAD 2')
        self.pdp.memory[2] = 1
        self.pdp.run(stepping=True)
        self.check(accumulator=octal('010'), link=0)

    def test_tad_with_carry(self):
        self.pdp.accumulator = octal('7777')
        self.pdp.memory[0] = self.instruction('TAD 2')
        self.pdp.memory[2] = 1
        self.pdp.run(stepping=True)
        self.check(accumulator=0, link=1)

    def test_isz_no_skip(self):
        self.pdp.memory[0] = self.instruction('ISZ 2')
        self.pdp.memory[2] = 1
        self.pdp.run(stepping=True)
        self.check(memory={2:2},pc=1)

    def test_isz_with_skip(self):
        self.pdp.memory[0] = self.instruction('ISZ 2')
        self.pdp.memory[2] = -1
        self.pdp.run(stepping=True)
        self.check(memory={2:0},pc=2)

    def test_dca(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('DCA 2')
        self.pdp.memory[2] = -1
        self.pdp.run(stepping=True)
        self.check(memory={2:1}, pc=1, accumulator=0)

    def test_jms(self):
        self.pdp.memory[0] = self.instruction('JMS 2')
        self.pdp.memory[2] = 0
        self.pdp.run(stepping=True)
        self.check(memory={2:1}, pc=3)

    def test_jmp(self):
        self.pdp.memory[0] = self.pal.instruction('JMP 2')
        self.pdp.run(stepping=True)
        self.check(pc=2)

    def test_indirection_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[0] = self.instruction('AND I 2')
        self.pdp.memory[2] = 3
        self.pdp.memory[3] = 4
        self.pdp.run(stepping=True)
        self.check(accumulator=4)

    def test_p_zero_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('AND Z 2')
        self.pdp.memory[2] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(accumulator=4)

    def test_page_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('AND 2') # in page 1
        self.pdp.memory[octal('202')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(accumulator=4)

    def test_indirect_and_page_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('AND I 2') # in page 1
        self.pdp.memory[octal('202')] = octal('203')
        self.pdp.memory[octal('203')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(accumulator=4)

    def test_indirect_and_zero_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('AND I Z 2') # 2 in page 0
        self.pdp.memory[2] = octal('203')
        self.pdp.memory[octal('203')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(accumulator=4)

    def test_indirection_assignment(self):
        self.pdp.accumulator = 7
        self.pdp.memory[0] = self.pal.instruction('DCA I 2')
        self.pdp.memory[2] = 3
        self.pdp.memory[3] = 4
        self.pdp.run(stepping=True)
        self.check(memory={3:7}, accumulator=0)

    def test_p_zero_assignment(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('DCA Z 2')
        self.pdp.memory[2] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(memory={2:7}, accumulator=0)

    def test_page_assignment(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('DCA 2') # in page 1
        self.pdp.memory[octal('202')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.check(memory={octal('202'):7}, accumulator=0)

    def test_indirect_and_page_assignment(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('DCA I 2') # in page 1
        self.pdp.memory[octal('202')] = octal('203')
        self.pdp.memory[octal('203')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.checker.check(memory={octal('203'):7}, accumulator=0)

    def test_indirect_and_zero_assignment(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.instruction('DCA I Z 2') # 2 in page 0
        self.pdp.memory[2] = octal('203')
        self.pdp.memory[octal('203')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.checker.check(memory={octal('203'):7}, accumulator=0)


class OprGroup1Test(TestCase):
    def setUp(self):
        self.pdp = PDP8()
        self.checker = ConfigChecker(self.pdp)
        self.pal = Pal()

    def instruction(self, text):
        return self.pal.instruction(text)

    def check(self, memory=None, pc=None, accumulator=None, link=None):
        self.checker.check(memory, pc, accumulator, link)

    def test_nop1(self):
        self.pdp.memory[0] = self.instruction('NOP')
        self.pdp.run(stepping=True)
        self.check(pc=1, accumulator=0, link=0)

    def test_cla1(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('CLA')
        self.pdp.run(stepping=True)
        self.check(accumulator=0, link=0)

    def test_cll(self):
        self.pdp.link = 1
        self.pdp.memory[0] = self.instruction('CLL')
        self.pdp.run(stepping=True)
        self.check(accumulator=0, link=0)

    def test_cla_and_cll(self):
        self.pdp.link = 1
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('CLA CLL')
        self.pdp.run(stepping=True)
        self.check(accumulator=0, link=0)

    def test_cll_and_cla(self):
        self.pdp.link = 1
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('CLL CLA')
        self.pdp.run(stepping=True)
        self.check(accumulator=0, link=0)

    def test_cma(self):
        self.pdp.link = 1
        self.pdp.accumulator = 0
        self.pdp.memory[0] = self.instruction('CMA')
        self.pdp.run(stepping=True)
        self.check(accumulator=octal('7777'), link=1)

    def test_cml0(self):
         self.pdp.link = 0
         self.pdp.accumulator = 0
         self.pdp.memory[0] = self.instruction('CML')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('0'), link=1)

    def test_cml1(self):
         self.pdp.link = 1
         self.pdp.accumulator = 0
         self.pdp.memory[0] = self.instruction('CML')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('0'), link=0)

    def test_rar00(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RAR')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('3777'), link=1)

    def test_rar01(self):
         self.pdp.link = 1
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RAR')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7777'), link=1)

    def test_rar10(self):
         self.pdp.link = 1
         self.pdp.accumulator = octal('7776')
         self.pdp.memory[0] = self.instruction('RAR')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7777'), link=0)

    def test_rar11(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7776')
         self.pdp.memory[0] = self.instruction('RAR')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('3777'), link=0)

    def test_rtr(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RTR')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('5777'), link=1)

    def test_ral00(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RAL')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7776'), link=1)

    def test_ral01(self):
         self.pdp.link = 1
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RAL')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7777'), link=1)

    def test_ral10(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('3777')
         self.pdp.memory[0] = self.instruction('RAL')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7776'), link=0)

    def test_ral11(self):
         self.pdp.link = 1
         self.pdp.accumulator = octal('3777')
         self.pdp.memory[0] = self.instruction('RAL')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7777'), link=0)

    def test_rtl(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RTL')
         self.pdp.run(stepping=True)
         self.check(accumulator=octal('7775'), link=1)

    def test_iac0(self):
         self.pdp.link = 0
         self.pdp.accumulator = 0
         self.pdp.memory[0] = self.instruction('IAC')
         self.pdp.run(stepping=True)
         self.check(accumulator=1, link=0)

    def test_iac1(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('IAC')
         self.pdp.run(stepping=True)
         self.check(accumulator=0, link=1)

    def test_iar(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('7777')
         self.pdp.memory[0] = self.instruction('RAL IAC') # IAC should execute first!
         self.pdp.run(stepping=True)
         self.check(accumulator=1, link=0)

    def test_g1order(self):
         self.pdp.link = 0
         self.pdp.accumulator = octal('1234')
         # order should be CLA (ac=0); CMA (ac = 7777), IAC (acc=0, link = 1), RAL (acc = 1, link =0)
         self.pdp.memory[0] = self.instruction('RAL IAC CLA CMA') #
         self.pdp.run(stepping=True)
         self.check(accumulator=1, link=0)


class OprGroup2Test(AbstractCodeTest):
    def test_halt(self):
        self.pdp.tracer = HaltTracer()
        self.pdp.memory[0] = self.instruction('HLT')  #
        self.pdp.run(stepping=True)
        assert_that(self.pdp.tracer.halted,'PDP8 should have executed HLT')

    def test_sma(self):
        self.pdp.accumulator = octal('7777') # -1
        self.pdp.memory[0] = self.instruction('SMA')
        self.pdp.run(stepping=True)
        self.check(pc=2)

    def test_sza(self):
        self.pdp.accumulator = 0
        self.pdp.memory[0] = self.instruction('SZA')
        self.pdp.run(stepping=True)
        self.check(pc=2)


    def test_snl(self):
        self.pdp.link = 1
        self.pdp.memory[0] = self.instruction('SNL')
        self.pdp.run(stepping=True)
        self.check(pc=2)

    def test_spa(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('SPA')
        self.pdp.run(stepping=True)
        self.check(pc=2)

    def test_sna(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('SNA')
        self.pdp.run(stepping=True)
        self.check(pc=2)

    def test_szl(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.instruction('SZL')
        self.pdp.run(stepping=True)
        self.check(pc=2)


























