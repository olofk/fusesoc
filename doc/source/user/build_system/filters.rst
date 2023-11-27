.. _ug_build_system_filters:

Filters: Make system-wide modifications to the EDAM structure
=============================================================

The last thing FuseSoC does before handing over to Edalize, is to prepare an EDAM file containing a description of the complete system and everything that the EDA tools need to know. It is sometimes useful to make system-wide changes after the system is assembled, and this is where filters come in. Filters are additional tasks that can be run to analyze and modify the EDAM structure, and through that structure the filters have access to the complete dependency tree and all source files.

FuseSoC ships with a few built-in filters for generally useful tasks:

* autotype: Sets file types according to the file name prefix for files that don't have an explicit file type set.
* custom: Runs the command specified with the environment variable `FUSESOC_CUSTOM_FILTER`. Two arguments are passed to the command. The first specifies the EDAM (yaml) file the custom command is supposed to read. The second specifies the name of the file that the filter should use to return the modified EDAM struct.
* dot: Creates a GraphViz dot file of the dependency tree

All filters are run from the work root directory.

.. note::
    Technically, an Edalize frontend can perform the exact same task as a FuseSoC EDAM filter. The difference is more philosophical in that a filter can be seen as something that fixes up the system before it is ready to be consumed by an EDA tool, while an Edalize frontend typically *is* an EDA tool. The filters will also possibly have access to more FuseSoC internals in the future.

Using filters
-------------

There are three way to enable which filters to be applied. These three options have various use-cases.

Filters in targets
~~~~~~~~~~~~~~~~~~

Filters specified in a target section of a core are typically required for the the build to work. In order to enable a filter for a target, add a list of filters using the `filters` key.

.. code-block:: yaml

   # An excerpt from a core file.
   targets:
     sim:
       # ...
       filters: [autotype, dot] # Apply the autotype and dot filters in that order

Filters in the configuration file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Filters can be set in the configuration file as a list of space-separated strings in the `main` section. These can be set with the fusesoc config cli, e.g. `fusesoc config filters "filter1 filter2"`. Filters set in the config file are typically used when all targets of the cores in the workspace need some filter to be applied, or just as a convenienence for users who like to have som particular filter always enabled. These filters are applied after the ones from the core file targets.

Filters on the command-line
~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is also possible to set filters on the command-line. This is typically used for one-off filters, e.g. to generate some debug info. They are enabled with the `--filter` parameters, e.g. `fusesoc run --filter=dot --target=sim ...`. The `--filter` parameter can be specified multiple times to add more filters. Filters on the command-line are applied after the ones from the configuration file.


Creating additional filters
---------------------------

A filter is a Python module that contains a class with the same name as the module, but capitalized. The class needs to implement a function called `run` which takes the EDAM struct as the first argumen and the work root as the second argument. The function needs to return the new EDAM struct even if it is unmodified.

Filter template::

    import logging
    import os

    logger = logging.getLogger(__name__)


    class Customfilter:
        def run(self, edam, work_root):
            # Print file sizes of all verilog files in the system
            for f in edam["files"]:
                if f["file_type"].startswith("verilogSource"):
                    size = os.path.getsize(os.path.join(work_root, f["name"]))
                    print(f"{f['name']} is {size} bytes")

            # Add an additional parameter
            edam["parameters"]["my_number"] = {"datatype" : "int",
                                               "paramtype": "vlogdefine",
                                               "default" : 5446}

            # Change the system name
            edam["name"] = "bestsystemever"

            # Return modified EDAM struct
            return edam

FuseSoC implements support for implicit namespace packages (https://peps.python.org/pep-0420/) This means that subclasses that logically belong to FuseSoC can be distributed over several physical locations and is something we can take advantage of to add new filters outside of the FuseSoC code base.

In order to do that we will create a directory structure that mirrors the structure of FuseSoC like the example below::

  externalplugin/
      fusesoc/
          filters/
	      customfilter.py
	      anothercustomfilter.py

There are two common options for making the above `customfilter.py` and `anothercustomfilter.py` available to FuseSoC.

The first way is to add the `externalplugin` path to ``PYTHONPATH``. The other is to add a `setup.py` in the `externalplugin` directory and install the filter plugin with pip as with other Python packages.

A `setup.py` in its absolutely most minimal form is listed below and is enough to install the plugin as a package in development mode using ``pip install --user -e .`` from the `externalplugin` directory.::

  from setuptools import setup
  setup()

A real `setup.py` like the one used by FuseSoC normally contains a lot more information.
