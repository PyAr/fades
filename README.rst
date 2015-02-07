fades
=====

FAst DEpendencies for Scripts


What does it do?
----------------

*fades* will automagically create a new virtualenv (or reuse a previous
created one for your script), installing or updating the necessary
dependencies, and execute your script inside that virtualenv, with the
only requirement of executing the script with *fades* and also marking
the required dependencies.


How to use it?
==============

When you write an script, you have to take two special measures:

- need to execute it with *fades* (not *python*)

- need to mark those dependencies

At the moment you execute the script, fades will create (if needed) a
virtualenv, install/update/remove dependencies (if needed), and execute
the script in that environment.


How to execute the script with fades?
-------------------------------------

You can always call your script directly with fades::

    fades myscript.py

However, for you to not forget about fades and to not execute it
directly with python, it's better if you put at the beggining of
the script the indication for the operating system that it should
be executed with fades... ::

    #!/usr/bin/fades

...and also set the executable bit in the script::

    chmod +x yourscript.py


How to mark the dependencies to be installed?
---------------------------------------------

The procedure to mark a module imported by the script as a *dependency
to be installed by fades* is by using a comment.

This comment will normally be in the same line of the import (recommended,
less confusing and less error prone in the future), but it also can be in
the previous one.

The simplest comment is like::

    import somemodule   # fades.pypi
    from somepackage import othermodule    # fades.pypi

The ``fades.pypi`` is mandatory, it may allow more options in the future.

With that comment, *fades* will install automatically in the virtualenv the
``somemodule`` or ``somepackage`` from PyPI.

Also, you can indicate a particular version condition, examples::

    import somemodule   # fades.pypi == 3
    import somemodule   # fades.pypi >= 2.1


How to control the virtualenv creation and usage?
-------------------------------------------------

You can influence several details of all the virtualenv related process.

*Note: the functionality in this parragraph is still not ready*.
The most important detail is which version of Python will be used in
the virtualenv. Of course, the corresponding version of Python needs to
be installed in your system, but you can control exactly which one to use.

*Note: the functionality in this parragraph is still not ready*.
No matter which way you're executing the script (see above), you can
pass a ``-p`` or ``--python`` argument, indicating the Python version to
be used just with the number (``2.7``), the whole name (``python2.7``) or
the whole path (``/usr/bin/python2.7``).

Other detail is the verbosity of *fades* when telling what is doing. By
default, *fades* only will use stderr to tell if a virtualenv is being
created, and to let the user know that is doing an operation that
requires an active network connection (e.g. installing a new depenency).

If you call *fades* with ``-v`` or ``--verbose``, it will send all internal
debugging lines to stderr, which may be very useful if any problem arises.
On the other hand if you pass the ``-q`` or ``--quiet`` parameter, *fades*
will not show anything (unless it has a real problem), so the original
script stderr is not polluted at all.


How to install it
=================

The classical way is to branch the project and run ``setup.py``::

    git clone https://github.com/PyAr/fades.git
    cd fades
    ./setup.py install

Other methods soon! Keep tuned...


Can I try it without installing it?
-----------------------------------

Yes! Branch the project and use the executable::

    git clone https://github.com/PyAr/fades.git
    cd fades
    bin/fades your_script.py


More help
=========

Some questions, hints, etc...

- *Everytime I edit my script with vim/gvim, ``fades`` installs everything again*: this is because vim doesn't keep extended attributes in the mambo-jambo it does when saving; to fix this add ``set backupcopy=yes`` in your ``$HOME/.vimrc`` file.


Even more help
--------------

You can ask any question or send any recommendation or request to the `mailing list <http://listas.python.org.ar/mailman/listinfo/fades>`_.

Also, you can open an issue `here <https://github.com/PyAr/fades/issues/new>`_ (please do if you find any problem!).

Thanks in advance for your time.
