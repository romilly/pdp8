# PDP8-Py

A Python emulator for DEC's PDP8-S computer.

## Why another emulator?

There are already several emulators for the PDP-8.

The most
[widely known emulator](https://www.raspberrypi.org/blog/pidp-8i-remaking-the-pdp-8i/)
is written in C.

Many Pi users (myself among them) are more comfortable with Python,
and writing my own emulator seemed the best way of making sure I really
understood how the PDP-8 worked.

## Requirements

The project was developed using Python 3.5. The assembler depends on
[reggie-dsl](https://pypi.org/project/reggie-dsl).

## Current Status

The emulator and its assembler (also written in Python) are almost complete
and they can run many of the sample programs in DEC's 1969 *Introduction to Programming*.

I have not yet implemented auto-increment registers but I hope to do so soon.

The emulator currently supports a tape reader and punch, but it does not implement any
of the optional features, nor does it yet support disk operations.

Test coverage is heading towards 100% but the code is largely uncommented.

I will add comments and documentation as time permit.

I have a number of follow-on projects in mind.
These are outlined in ROADMAP.md.




