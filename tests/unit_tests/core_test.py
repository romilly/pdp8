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



