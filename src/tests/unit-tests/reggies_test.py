from unittest import TestCase

from hamcrest import equal_to
from hamcrest.core import assert_that

from pdp8.reggies import *


class ReggiesTest(TestCase):
    def test_matches_digit(self):
        term = digit
        assert_that(term.matches('1'))
        assert_that(term.matches('11'), equal_to(None))
        assert_that(term.matches('A'), equal_to(None))

    def test_matches_digits(self):
        term = digits
        assert_that(term.matches('1'))
        assert_that(term.matches('12'))
        assert_that(term.matches('A'), equal_to(None))

    def test_capital(self):
        term = capital
        assert_that(term.matches('A'))
        assert_that(term.matches('a'), equal_to(None))
        assert_that(term.matches('A1'), equal_to(None))
        assert_that(term.matches('1'), equal_to(None))

    def test_or(self):
        term = capital | digit
        assert_that(term.matches('A'))
        assert_that(term.matches('1'))
        assert_that(term.matches('a'), equal_to(None))
        assert_that(term.matches('A1'), equal_to(None))


    def test_add(self):
        term = capital + digit
        assert_that(term.matches('A1'))
        assert_that(term.matches('a'), equal_to(None))
        assert_that(term.matches('1'), equal_to(None))
        assert_that(term.matches('1A'), equal_to(None))

    def test_text(self):
        term = plus
        assert_that(term.matches('+'))
        assert_that(term.matches('A'), equal_to(None))
        assert_that(term.matches('1'), equal_to(None))

    def test_optional(self):
        term = optional(capitals)
        assert_that(term.matches(''))
        assert_that(term.matches('A'))
        assert_that(term.matches('AA'))
        assert_that(term.matches('1'), equal_to(None))



