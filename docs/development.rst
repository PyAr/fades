How to develop fades itself
===========================

Quick guide to get you up and running in fades development.


Getting the code
----------------

Clone the project::

    git clone git@github.com:PyAr/fades.git


Install dependencies
--------------------

*fades* manages it's own dependencies, so there is nothing extra you need to install.


How to run the tests
--------------------

When starting development, at all times, and specially before wrapping up
a new branch, you need to be sure that all tests pass ok.

This is very simple, actually, just run::

    ./test

That will not only check test cases, but also that the code complies with
aesthetic recommendations, and that the README document has a proper format.

If you want to run *one* particular test, just specify it. Example::

    ./test tests.test_main:DepsMergingTestCase.test_two_different


Development process
-------------------

Just pick an issue from `the list <https://github.com/PyAr/fades/issues>`_.

Develop, assure ``./test`` is happy, commit, push, create a pull request, etc.

Please, if you aim for creating a Pull Request with new code (functionality
or fixes), include tests for your changes.

Thanks! Enjoy.
