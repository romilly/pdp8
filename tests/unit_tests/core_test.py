from unittest import TestCase

from pdp8.core import PDP8, octal
from pdp8.pal import Pal
from tests.helpers.checker import ConfigChecker


class MriTest(TestCase):
    def setUp(self):
        self.pdp = PDP8()
        self.checker = ConfigChecker(self.pdp)
        self.pal = Pal()

    def test_and(self):
        self.pdp.accumulator = octal('7070')
        self.pdp.memory[0] = self.pal.instruction('AND 2')
        self.pdp.memory[2] = octal('1120')
        self.pdp.run(stepping=True)
        self.checker.check(accumulator=octal('1020'))

    def test_tad(self):
        self.pdp.accumulator = octal('007')
        self.pdp.memory[0] = self.pal.instruction('TAD 2')
        self.pdp.memory[2] = 1
        self.pdp.run(stepping=True)
        self.checker.check(accumulator=octal('010'))

    def test_isz_no_skip(self):
        self.pdp.memory[0] = self.pal.instruction('ISZ 2')
        self.pdp.memory[2] = 1
        self.pdp.run(stepping=True)
        self.checker.check(memory={2:2},pc=1)

    def test_isz_with_skip(self):
        self.pdp.memory[0] = self.pal.instruction('ISZ 2')
        self.pdp.memory[2] = -1
        self.pdp.run(stepping=True)
        self.checker.check(memory={2:0},pc=2)

    def test_dca(self):
        self.pdp.accumulator = 1
        self.pdp.memory[0] = self.pal.instruction('DCA 2')
        self.pdp.memory[2] = -1
        self.pdp.run(stepping=True)
        self.checker.check(memory={2:1}, pc=1, accumulator=0)

    def test_jms(self):
        self.pdp.memory[0] = self.pal.instruction('JMS 2')
        self.pdp.memory[2] = 0
        self.pdp.run(stepping=True)
        self.checker.check(memory={2:1}, pc=3)

    def test_jmp(self):
        self.pdp.memory[0] = self.pal.instruction('JMP 2')
        self.pdp.run(stepping=True)
        self.checker.check(pc=2)

    def test_indirection_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[0] = self.pal.instruction('AND I 2')
        self.pdp.memory[2] = 3
        self.pdp.memory[3] = 4
        self.pdp.run(stepping=True)
        self.checker.check(accumulator=4)

    def test_page_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.pal.instruction('AND Z 2') # in page 1
        self.pdp.memory[octal('202')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.checker.check(accumulator=4)

    def test_i_and_z_reference(self):
        self.pdp.accumulator = 7
        self.pdp.memory[octal('200')] = self.pal.instruction('AND I Z 2') # in page 1
        self.pdp.memory[octal('202')] = octal('203')
        self.pdp.memory[octal('203')] = 4
        self.pdp.run(start=octal('200'), stepping=True)
        self.checker.check(accumulator=4)





