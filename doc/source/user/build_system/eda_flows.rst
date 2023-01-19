.. _ug_build_system_eda_flows:

Interfacing EDA tool flows
==========================

A design described by FuseSoC core description files is intended to be used by one or more EDA tools such as simulators, synthesis tools, linters etc. FuseSoC uses `Edalize <https://github.com/olofk/edalize>`_ to configure and run EDA tools. FuseSoC users still need to select which EDA tool or flow of tools to be run and in many cases also provide configuration to Edalize. This is done from the target section of the core description files.

.. note::

Edalize currently exposes two different APIs called the *tool API* and *flow API* respectively. These have different configuration keys in the core description files. The new flow API is intended to become the default API. However, not all Edalize backends have been converted to the new API, so the old tool API remains in use. If both the `default_tool` key (from the tool API) and the `flow` key (from the flow API) is defined in a target, the flow API will take precedence.

.. toctree::
   :maxdepth: 2
   :caption: Using the Edalize tool interfacing APIs

   flow_options.rst
   tool_options.rst



.. note::

   Where to find tool- or flow-specific code in FuseSoC

   The tool- and flow-specific code is provided by the `Edalize library <https://github.com/olofk/edalize>`_.
   Most files, such as project files and Makefiles, are templates within edalize and can be improved easily if necessary.
   Please open an issue at the `edalize issue tracker on GitHub <https://github.com/olofk/edalize/issues>`_ to suggest improvements to tool-specific code.
