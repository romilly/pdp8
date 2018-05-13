from io import StringIO
from unittest import TestCase

from helpers.checker import PDPChecker
from pdp8.core import PDP8, octal
from pdp8.pal import Pal
from pdp8.tracing import PrintingTracer


def read(filename):
    with open('data/'+filename) as f:
        data = f.read()
    return data


class PalTest(TestCase):
    def setUp(self):
        self.pdp8 = PDP8()
        self.pal = Pal(self.pdp8)
        self.checker = PDPChecker(self.pdp8)

    def test_assembles_mult(self):
        self.pal.assemble(StringIO(read('mult.pal')))
        self.pdp8.run(start=octal('200'), debugging=True)
        self.checker.check(accumulator=648)

    def test_assembles_mul_sub(self):
        self.pal.assemble(StringIO(read('mul-sub.pal')), list_symbols=True)
        self.pdp8.run(start=octal('200'), debugging=True)
        self.checker.check({136: 6})
    #
    # def test_assembles_hw(self):
    #     self.pal.assemble(StringIO(read('hello.pal')), list_symbols=True)
    #     self.pdp8.run(start=octal('200'), debugging=True)
    #     self.checker.check(output='HELLO, WORLD!\r\n')

    def test_assembles_one_char(self):
        self.pal.assemble(StringIO(read('one_char.pal')), list_symbols=True)
        self.pdp8.run(start=octal('200'), debugging=True)
        self.checker.check(output='A')

    def test_search_1234(self):
        self.pal.assemble(StringIO(read('search-1234.pal')), list_symbols=True)
        self.pdp8.run(start=octal('200'), debugging=False)
        self.checker.check(accumulator=0)

    def test_isz(self):
        self.pal.assemble(StringIO(read('isz-test.pal')), list_symbols=True)
        self.pdp8.run(start=octal('200'), debugging=True)
        self.checker.check(accumulator=0)
