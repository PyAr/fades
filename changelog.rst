Change Log
==========

All notable changes to fades will be documented in this file.

Release 2.0 [27/02/2015]
------------------------

Changed
~~~~~~~

* Fades stopped using xattr and now is storing venvs metadata on a json encode file. `#29 <https://github.com/PyAr/fades/issues/29>`_  
  Now you can think fades as a venvs cache. The venv isn't directly linked to a script. 
  Fades has a venvs database and search in it for a venv that fulfill the marked dependencies 
  and if it doesn't exist will create one.
* ``pkg_resources`` from ``setuptools`` is now a dependency.


Fixed
~~~~~

* Improvements and fixes on parsing and dependencies comparison. #17, #33, #37, #41, #43 and #50
* Other minors bugs.

Check the full list of issues on this release `here <https://github.com/PyAr/fades/issues?q=is%3Aissue+milestone%3A%22Release+2%22+is%3Aclosed+sort%3Acreated-asc>`_


Release 3.0 [unreleased]
------------------------

Assigned issues to this release `here <https://github.com/PyAr/fades/issues?q=is%3Aopen+is%3Aissue+milestone%3A%22Release+3%22>`_
