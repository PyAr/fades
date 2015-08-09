How to develop fades itself
===========================

Quick guide to get you up and running in fades development.


Getting the code
----------------

Clone the project::

    git clone git@github.com:PyAr/fades.git


Install dependencies
--------------------

Fades depends on several packages for development, here are the
instructions to install them for each OS.

- Ubuntu/Debian::

    apt-get install python-xdg python3-nose python3-flake8

- And on Archlinux with::

    pacman -S python-xdg python-nose flake8

Also, you need to install a package from PyPI, do the following
with ``sudo`` if you'll install it at system level, or just as it is
to install it in a virtualenv::

    pip3 install logassert


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
