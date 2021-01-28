.. _ug_installation:

******************
Installing FuseSoC
******************

FuseSoC is written in Python and runs on all major operating systems.

System Requirements
===================

Before installing FuseSoC check your system requirements.

- Operating System: Linux, Windows, macOS
- Python 3.5 or newer.
  (The last version supporting Python 2.7 is FuseSoC 1.10.)
- The Python packages ``setuptools`` and ``pip`` need to be installed for Python 3.

Installation under Linux
========================

.. note::

   Do not type the ``$`` symbol shown in the instructions below.
   The symbol indicates that the command is to be typed into a terminal window.
   Lines not prefixed with ``$`` show the output of the command.
   Depending on your system, the output might be different.

FuseSoC is provided as ``fusesoc`` Python package and installed through pip, the Python package manager.
The steps below cover the most common installation cases.
Refer to the pip documentation for more advanced installation scenarios.

FuseSoC, like all Python packages, can be installed for the current user, or system-wide for all users.
The system-wide installation typically requires root permissions.

Installation for the current user
---------------------------------

To install the current stable version of FuseSoC for the current user, open a terminal window and run the following command.
If an older version of FuseSoC is found, this version is upgraded to the latest stable release.

.. code-block:: shell-session

   $ pip3 install --upgrade --user fusesoc

Check that the installation worked by running

.. command-output:: fusesoc --version


If this command works FuseSoC is installed properly and ready to be used.

If the terminal reports an error about the command not being found check that the directory ``~/.local/bin`` is in your command search path (``PATH``), or perform a system-wide installation instead (see below).


System-wide installation
------------------------

FuseSoC can be installed for all users on a system.
This operation typically requires root permissions.

.. code-block:: shell-session

   $ sudo pip3 install --upgrade fusesoc

Uninstalling FuseSoC
--------------------

Use ``pip`` to remove FuseSoC from your system.

.. code-block:: shell-session

   $ pip3 uninstall fusesoc


Installation under Windows
==========================

.. todo::

    Add Windows installation instructions.


Installation under macOS
========================

.. todo::

    Add macOS installation instructions.
