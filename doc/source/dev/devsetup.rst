Development Setup
=================

.. note::

   To make changes to a backend, e.g. to the way a simulator or synthesis tool is called, you need to modify edalize, not fusesoc.
   Edalize is a separate project, see https://github.com/olofk/edalize for more information.

Get the code
------------

The FuseSoC source code is maintained in a git repository hosted on GitHub.
To improve FuseSoC itself, or to test the latest unreleased version, it is necessary to clone the git repository first.

.. code-block:: bash

   cd your/preferred/source/directory
   git clone https://github.com/olofk/fusesoc


Setup development environment
-----------------------------

.. note::

   If you have already installed FuseSoC, remove it first using ``pip3 uninstall fusesoc``.

To develop FuseSoC and test the changes, the fusesoc package needs to be installed in editable or development mode.
In this mode, the ``fusesoc`` command is linked to the source directory, and changes made to the source code are immediately visible when calling ``fusesoc``.

.. code-block:: bash

   # Install all Python packages required to develop fusesoc
   pip3 install --user -r dev-requirements.txt

   # Install the fusesoc package in editable mode
   pip3 install --user -e .

.. note::

    All commands above use Python 3 and install software only for the current user.
    If, after this installation, the ``fusesoc`` command cannot be found adjust your ``PATH`` environment variable to include ``~/.local/bin``.

After this installation is completed, you can

* Edit files in the source directory and re-run fusesoc to immediately see the changes.
* Run the unit tests as outlined in the section below.

You can now modify the Python files in the source tree, and re-run ``fusesoc`` to test the changes.


Running tests
-------------

The FuseSoC contains unit tests written using the pytest framework.

.. code-block::

   cd fusesoc/source/directory

   # run all tests
   python3 -m pytest

   # run a single test: use filename::method_name, e.g.
   python3 -m pytest tests/test_capi2.py::test_capi2_get_tool --verbose

Refer to the `pytest documentation <https://docs.pytest.org/en/latest/>`_ for more information how tests can be run.

.. note::

    In many installations you can replace ``python3 -m pytest`` with the shorter ``pytest`` command.
