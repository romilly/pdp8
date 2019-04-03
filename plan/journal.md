# Journal for PDP8 project

## Wednesday 03 April 2019

I need to jiggle things around a bit to reflect the necessary changes to reggie-dsl.

I've committed the project and reggie in their current state before the refactoring.

Next:
1. In `pdp8`, remove the dependency on the reggie-dsl package
2. Replace it by adding reggie to the project in PyCharm
3. Refactor `match` to `match_line` in the project(s)
    1. Ensure that documentation, including examples, is included
3. Run tests
    1. In `pdp8`
    2. In `reggie`
4. Commit both and push.
5. Remove the reggie project from pdp8 in pycharm
6. Update `reggie-dsl` on PyPi
7. Add dependency on PyPi package in `pdp8` and re-run tests

Then I can complete the updates/extensions
to `reggie-dsl` prior to work on `apl-reggie`.


