FuseSOC: Tool options
=====================

In the last tutorial we created a simple core with a testbench and executed this. It's now time to look at some features that make it more obvious why we want to use FuseSoC instead of just writing a script that launches Icarus Verilog with our two verilog files. Perhaps the most immediately useful thing is to take advantage of FuseSoC's role as an abstraction layer for different EDA tools. In tutorial 1 we saw how to run a testbench in different simulators by just changing the --tool option to modelsim, xsim, isim or rivierapro. That won't work this time however. Running with modelsim or xsim will produce errors from the tools complaining that timescale is not set for all units. Verilog's system of time units and precision is quite annoying and highly tool-specific. We won't dig deeper into that now, but just present a way to get around the problem by specifying a default timescale for the complaining tools. Now, FuseSoC doesn't have a dedicated way to set timescale, but any tool-specific options can be supplied through a special tools section. To set a default timescale for modelsim and xsim we would add this to our .core file

targets: sim: tools: modelsim: vlog\_options: [-timescale=1ns/1ns] xsim: xelab\_options: [--timescale, 1ns/1ns]

Running the simulation with modelsim or xsim should now work. Other common uses of tool-specific options is to suppress certain warnings or include vendor-provided libraries. We now know that the testbench works with multiple tools, but we most of the time we are happy to use Icarus Verilog. To save us from writing ``--tool=icarus`` all the time we will therefore set a default tool for our ``sim`` target and the complete core file will at this point look like this:

.. code:: yaml

    CAPI=2:
    name : ::blinky:0

    filesets:
      rtl:
        files:
          - pps.v : {file_type : verilogSource}

      tb:
        files:
          - pps_tb.v : {file_type : verilogSource}

    targets:
      sim:
        default_tool: icarus
        filesets : [rtl, tb]
        tools:
          modelsim:
            vlog_options: [-timescale=1ns/1ns]
          xsim:
            xelab_options: [--timescale, 1ns/1ns]
        toplevel: pps_tb
