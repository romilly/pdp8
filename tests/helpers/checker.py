from hamcrest import assert_that
from hamcrest.core.base_matcher import BaseMatcher


class AddressMatcher(BaseMatcher):
    def __init__(self, address, contents):
        self.address = address
        self.contents = contents

    def _matches(self, pdp8):
        return pdp8[self.address] == self.contents

    def describe_to(self, description):
        description.append('pdp8[%d]=%d ' % (self.address, self.contents ))

    def describe_mismatch(self, pdp8, mismatch_description):
        mismatch_description.append_text('pdp8[%d]=%d' % (self.address, pdp8[self.address]))

def memory_contains(address, contents):
    return AddressMatcher(address, contents)


class ConfigChecker(object):
    def __init__(self, pdp8):
       self.pdp8 = pdp8

    def check(self, memory=None, pc=None, accumulator=None, link=None):
        if memory is not None:
            for address in memory.keys():
                assert_that(self.pdp8, memory_contains(address, memory[address]))
        if pc is not None:
            assert_that(self.pdp8.pc == pc, 'expected pc=%d but pc=%d' % (pc, self.pdp8.pc))
        if accumulator is not None:
            assert_that(self.pdp8.accumulator == accumulator, 'expected ac=%d but ac=%d' % (accumulator, self.pdp8.accumulator))
        if link is not None:
            assert_that(self.pdp8.link == link, 'expected link=%d but link=%d' % (link, self.pdp8.link))


