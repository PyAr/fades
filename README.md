fades
=====

FAst DEpendencies for Scripts


What does it do?
----------------

When you execute your script with *fades*, it will automagically create 
a new virtualenv (or reuse a previous created one for that script), 
installing or updating the necessary dependencies, and execute your
script inside that virtualenv.

FIXME: tell how to mark the dependencies in the python script

FIXME: alert that when hitting the network to install/update dependencies it
will show information to stderr (-q can be used to avoid this).


How to use it?
--------------

FIXME write here:
 - that the script can be called directly:  fades myscript.py
 - that the script can have a  #!/usr/bin/fades  at the beginning
 - that if you call fades with -q it will never show anything to stderr
 - that if you call fades with -v will show all internal debugging lines to stderr!
