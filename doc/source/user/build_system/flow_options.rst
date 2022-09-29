.. _ug_build_system_flow_options:

Configuring a flow
==================

FuseSoC uses `Edalize <https://github.com/olofk/edalize>`_ to chain together and run EDA tools. Edalize supports many different EDA tools and combinations of tools working together, called flows. A flow could e.g. be an FPGA bitstream flow where one EDA tool is used for synthesis, another one for place & route and a third one to convert the P&R database into an image that can be loaded into the FPGA. Another example could be a simulation flow, where the simulator itself is just one tool, but where a code conversion tool is used to preprocess the input to the simulator, e.g. ghdl to convert VHDL to Verilog for tools that don't handle the former well enough.

FuseSoC abstracts away many differences between :term:`tools <tool>` and tries to provide sane defaults to build many designs out of the box with no further configuration required. However, not all tool-specific details can be hidden.

At the same time, a certain level of tool-specific configurability is required to make full use of the features available in different tools.

There are two categories of options available for the Edalize backends. *Flow options* that affect how the tools are chained together (the flow graph) and *tool options* for the individual tools to be run as part of the flow. This means that since the flow options influence which tools that will be run, some tool options only become available for certain combinations of flow options.

The example below shows how the `test` target selects and configures a flow. The `flow` key selectes the flow itself. The selected `sim` flow has a *flow option* called `sim` that decides which simulator to use. `iverilog_options` and `vlog_options` are tool options for Icarus Verilog and Siemens QuestaSim/ModelSim and will be passed to the approriate tool if it's in the flow graph.

This setup selects icarus as the tool, which means the `vlog_options` will not be used. However, all *flow options* and *tool options* are also automatically available on the command-line, which means that passing `--tool=modelsim` as a backend parameter will override the tool setting from the target. The same can be done for the two tool options, with the difference that for flow or tool option that are lists, any additional values passed on the command-line will append rather than replace the values in the core description file.

.. code-block:: yaml

   # An excerpt from a core file.
   # ...
   targets:
     test:
       # ...
       flow: sim
       flow_options:
           tool: icarus
           iverilog_options:
             - -g2012 # Use SystemVerilog-2012
           vlog_options:
             - -timescale=1ns/1ns

The available options for any flow can be found in the `Edalize <https://github.com/olofk/edalize>`_ documentation. They can also be found by running a target with the `--help` flag. `fusesoc run --target=<some target> <some core> --help`
