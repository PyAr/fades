Python and the Management of Dependencies
=========================================

Python has an extensive standard library ("batteries included!"), but is
frequent the necessity of using other modules not included there, mostly
from the Python Package Index (`PyPI <https://pypi.python.org/pypi>`_).

The original way of installing those modules is at "system level"
(`sudo pip install foobar`), in the operating system in a general way,
making them available to be used by any program that is executed.

Beyond needing root or administrator level to install the dependencies in
that way, the first problem we find are conflicts: the typical case of two
programs needing two different versions of the same dependency, which can
not be achieved when installing the dependencies globally.

This is why is so normal in Python to use "virtual environments" (or
"virtualenvs"). A new virtualenv is created for each program, the needed
dependencies for each program are installed in the corresponding virtualenv,
and as stuff in a virtualenv is only accessible from inside the virtualenv,
there are no conflicts anymore.

At this point, however, we hit the problem of the administration of the
virtualenvs themselves: create them, install modules in them, activate them
to be uses by each program and deactivate them later, remember the names of
each environment for each program, etc.

To automatize this, `fades <https://fades.readthedocs.org/>`_ was born.

*fades* allows you to unleash all the power of virtualenvs without needing
to worry about them.

Do you want to execute a script that needs the ``foobar`` dependency?
``fades -d foobar script.py``

Do you want an interactive interpreter having ``foobar`` installed as
dependency? ``fades -d foobar``

Do you need to execute the script but with several dependencies, one with
a specific version? ``fades -d foo -d bar -d baz==1.1 script.py``

Do you have all the dependencies in a requirements file?
``fades -r requirements.txt script.py``

These are only simple examples of what you can do with *fades*. Virtual
environments are a very powerful tool, and automate and simplify their
use makes *fades* to have a lot of options, some that you will use
everyday, others that will prove useful in some specific situations.

Start to use *fades* step by step (`check the docs
<https://fades.readthedocs.org/en/latest/readme.html>`_) and will find
that it will solve the dependencies management in your programs and
scripts, using virtualenvs but without the complexity of having to deal
with them by hand.
