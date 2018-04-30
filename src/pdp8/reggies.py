"""
regular expressions made easy-ish
"""
from abc import ABCMeta, abstractmethod
import re


def re_for(term):
    reexp = ncg(term).expr() + '$'
    return re.compile(reexp)


class Term():
    __metaclass__ = ABCMeta

    @abstractmethod
    def expr(self):
        pass

    def __add__(self, term):
        return Join(self, term)

    def __or__(self, term):
        return Or(self, term)

    def matches(self, text):
        rx = re.compile(re_for(self))
        return rx.match(text)

    def is_simple(self):
        return False

    def called(self, name):
        return NamedGroup(name, self)

    def names(self):
        return []


class Text(Term):
    def __init__(self, text):
        self.text = self.escape(text)

    def expr(self):
        return self.text

    def escape(self, text):
        return ''.join(self.escape_character(ch) for ch in text)

    def escape_character(self, ch):
        return ch if ch not in '.^$*+?{}[]\|()' else r'\%s' % ch


class Osp(Term):

    def expr(self):
        return '\s*'


class NamedGroup(Term):
    def __init__(self, name, term):
        self.name = name
        self.term = term

    def expr(self):
        return '(?P<%s>%s)' % (self.name, self.term.expr())

    def names(self):
        return [self.name]



class Character(Term):
    def expr(self):
        return '.'

    def is_simple(self):
        return True


class Multiple(Term):
    def __init__(self, term):
        self.term = ncg(term)

    def expr(self):
        return self.term.expr()+'+'

    def names(self):
        return self.term.names()


class Optional(Term):
    def __init__(self, option):
        self.option = ncg(option)

    def expr(self):
        return self.option.expr()+'?'

    def names(self):
        return self.option.names()


class BinaryTerm(Term):
    __metaclass__ = ABCMeta

    def __init__(self, left, right):
        self.left = left
        self.right = right

    @abstractmethod
    def expr(self):
        pass

    def names(self):
        return self.left.names()+self.right.names()


class Or(BinaryTerm):
    def __init__(self, left, right):
        BinaryTerm.__init__(self, left, right)

    def expr(self):
        return self.left.expr()+'|'+self.right.expr()


class Capital(Term):
    def expr(self):
        return '[A-Z]'

    def is_simple(self):
        return True


class Digit(Term):
    def expr(self):
        return '[0-9]'

    def is_simple(self):
        return True


class Join(BinaryTerm):
    def __init__(self, left, right):
        BinaryTerm.__init__(self, left, right)

    def expr(self):
        return self.left.expr()+self. right.expr()


def multiple(term):
    return Multiple(term)


def optional(term):
    return Optional(term)


def g(name, term):
    return NamedGroup(name, term)


class NonCapturingGroup(Term):
    def __init__(self, term):
        self.term = term

    def expr(self):
        return '(?:%s)' % self.term.expr()

    def names(self):
        return self.term.names()


def ncg(term):
    if term.is_simple():
        return term
    return NonCapturingGroup(term)


def text(text):
    return Text(text)

osp = Osp()


class Space(Term):
    def expr(self):
        return '\s'


class Texts(Term):
    def __init__(self, *texts):
        self.texts = texts

    def expr(self):
        return '(%s)' % '|'.join(self.texts)


def texts(*texts):
    return Texts(*texts)


space = Space()
plus = Text('+')
digit = Digit()
digits = multiple(digit)
capital= Capital()
capitals = multiple(capital)
character = Character()
characters = multiple(character)
an = digit | capital
identifier = capital + optional(multiple(an))
