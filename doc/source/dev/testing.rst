Testing
=======

The FuseSoC source code contains a large number of tests in the ``tests`` directory.
These tests use the `pytest framework <https://www.pytest.org>`_.

Running tests
-------------

To run the test `pytest must be installed <https://docs.pytest.org/en/latest/getting-started.html>`_ for Python 3, either through pip3, or (on Linux) as distribution package (often called ``python3-pytest``).

.. code-block::

   cd fusesoc/source/directory

   # The fusesoc package must be installed and importable before calling pytest.
   pip3 install -e .

   # run all tests
   python3 -m pytest

   # run a single test: use filename::method_name, e.g.
   python3 -m pytest tests/test_capi2.py::test_capi2_get_tool --verbose

Refer to the `pytest documentation <https://docs.pytest.org/en/latest/>`_ for more information how tests can be run.

.. note::

    In many installations you can replace ``python3 -m pytest`` with the shorter ``pytest`` command.
