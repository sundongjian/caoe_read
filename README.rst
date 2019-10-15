=======================================================
CaoE - Kill all children processes when the parent dies
=======================================================

CaoE makes it easy to automatically kills all spawned children (and
grandchildren) processes when the parent dies, even if killed by SIGKILL.

Usage
=====

Simply call::

  caoe.install()

at the beginning of your program.

How it works
============

When ``caoe.install()`` is called, it forks out a child process and a
grandchild process.  Both the parent and the child process will block, only the
grandchild process will continue to run.  The child process keeps checking the
status of parent.  If it found that the parent has died, it kills grandchild
process (and grand-grandchild processes if there are any) and suicides.

.. image:: https://secure.travis-ci.org/douban/CaoE.png?branch=develop
   :alt: Build Status
   :target: http://travis-ci.org/douban/CaoE

.. vim:set filetype=rst:


Change Log
==========

0.1.7
-----

* Fix a bug that child process will exit on any signal.
* Drop support for python 2.6.
* Use py.test and tox for test runner, drop dependency of nose.
* Make tests more stable.
