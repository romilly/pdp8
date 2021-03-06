# PDP8-Py

A Python emulator for DEC's PDP-8 computer.

[![Build status](https://travis-ci.org/romilly/pdp8.svg?master)](https://travis-ci.org/romilly)

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ff6e7cc106244d2ab0a27b0e5da0e096)](https://www.codacy.com/app/romilly/pdp8?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=romilly/pdp8&amp;utm_campaign=Badge_Grade)

## Why another emulator?

There are already several emulators for the PDP8.

The most
[widely known emulator](https://www.raspberrypi.org/blog/pidp-8i-remaking-the-pdp-8i/)
is written in C.

Many Pi users (myself among them) are more comfortable with Python,
and writing my own emulator seemed the best way of making sure I
understood how the PDP-8 worked.

## Requirements

The project was developed using Python 3.5. The assembler depends on
[reggie-dsl](https://pypi.org/project/reggie-dsl).

## Current Status

The emulator and its assembler (also written in Python) are almost complete
and they can run many of the sample programs in DEC's 1969 *Introduction to Programming*.

I have not yet implemented auto-increment registers but I will do so.

I have not yet implemented interrupts, partly because I am stuck working out how to do
create an end-to-end test.

I can write unit tests but these will just verify that I've written
the code they way I *think* the PDP8 works.

I need a known-good program to run that will
verify correct implementation. Suggestions welcome!

The emulator currently supports a tape reader and punch, but it does not implement any
of the optional features, nor does it yet support disk operations.

Test coverage is heading towards 100% but the code is largely uncommented for now.

I will add comments and documentation as time permits.

I have a number of follow-on projects in mind.
These are outlined in ROADMAP.md.




