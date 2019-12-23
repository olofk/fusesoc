Development Setup
=================

.. note::

   To make changes to a backend, e.g. to the way a simulator or synthesis tool is called, you need to modify edalize, not fusesoc.
   Edalize is a separate project, see https://github.com/olofk/edalize for more information.

Linux
-----

.. note::

   If you have already installed FuseSoC, remove it first using ``pip3 uninstall fusesoc``.

The FuseSoC source code is maintained in a git repository hosted on GitHub.
To improve FuseSoC itself, or to test the latest unreleased version, it is necessary to clone the git repository first.

.. code-block:: bash

   cd your/preferred/source/directory
   git clone https://github.com/olofk/fusesoc

FuseSoC then needs to be installed in editable or development mode.
In this mode, the ``fusesoc`` command is linked to the source directory, and changes made to the source code are immediately visible when calling ``fusesoc``.

.. code-block:: bash

   cd fusesoc
   # Use the ``--user`` flag to perform an installation for the current user;
   # remove this flag for a system-wide installation.
   pip3 install --editable --user .


You can now modify the Python files in the source tree, and re-run ``fusesoc`` to test the changes.
