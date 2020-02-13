FuseSOC: Creating a Core
========================

We covered the basics of core files and FuseSoC usage in `tutorial 1 <1-getting_started.md>`__. It's now time to use this knowledge to create our own core.

We will start by creating the PPS functionality described in tutorial 1. To get some indication if this works as intended we can connect the output to a LED (which should hopefully exist on every development board ever made). I will call this never-seen-before technological marvel Blinky (patent pending for "Device for changing luminosity of a solid state light source at a fixed inteval").

First thing to do is to create a new directory and put a file inside with a ``.core``. We will use the directory ``~/fusesoc_tutorial/cores/gpsemulator`` and name the file ``blinky.core``.

``blinky.core`` will look like this to begin with

.. code:: yaml

    CAPI=2:

    name : ::blinky:0

This is the minimal information we need in a core file. The CAPI header and a name for the core. If you now try to run ``fusesoc list-cores`` or ``fusesoc core-info blinky`` you will notice that the core cannot be found. This is because we haven't yet told FuseSoC where to look for the core.

There are two and a half way to make FuseSoC find the core. The first method is to specify it on the command-line. Assuming the aformentioned directory layout and that we run from the previously created workspace directory we can run ``fusesoc --cores-root=../cores core-info blinky``. As FuseSoC will recursively search for cores in a given path, it's fine to use the parent directory of the one containing the ``.core`` file. In fact, as we will grow our collection of cores over time it can be a good idea to put them all under the same parent directory to avoid having to specify many paths.

The --cores-root argument is transient, and FuseSoC will have forgotten all about it after it has finished its work. To avoid having to specify that argument all the time, we will instead register the directory as a library in a configuration file. One or more cores in a directory tree is called a library in FuseSoC terminology. To register the directory run ``fusesoc library add tutorial ../cores``.

Now you should be able to run ``fusesoc core-info blinky`` and FuseSoC will find the core.

Running ``fusesoc library add`` will have created a file called ``fusesoc.conf`` in the workspace directory looking something like this

::

    [library.tutorial]
    sync-type = local
    location = /home/user/fusesoc_tutorial/cores

We will not do an in-depth analysis of the configuration file right now, but just notice that every library has a name, passed as the first argument to ``fusesoc library add`` and in this case also a location. Now, if you run ``fusesoc list-cores`` there will be a lot more cores than just the one we added. Also, if you run ``fusesoc list-cores`` from another directory than the workspace directory, it will not find good ol' blinky. This is because FuseSoC normally reads the libraries from ``$XDG_CONFIG_HOME/fusesoc/fusesoc.conf`` and then from ``fusesoc.conf`` in the current directory. This makes it easy to have the cores from the standard libraries always available, but use different project-specific cores on top of that by using different workspaces. Running ``fusesoc --config=<config file>`` is a special case where *only* the libraries specified in that configuration file is used. If we run ``fusesoc --config=fusesoc.conf list-cores`` it will only list our blinky core. Finally, to add a library to the global configuration file, just run ``fusesoc library add --global <name> <location>``. That's enough about configuration files for a while. Let's start coding.

Now we can create the verilog module in ``pps.v`` within the gpsemulator core directory. Blinky needs a clock input, an output and an indication of the clock frequency to know how fast it should blink. It should look somewhat like this, assuming a default clock frequency of 50MHz

.. code:: verilog

    module pps
      #(parameter clk_freq_hz = 50_000_000)
       (input  clk,
        output reg pps_o = 1'b0);

       reg [$clog2(clk_freq_hz)-1:0] count = 0;

       always @(posedge clk) begin
          count <= count + 1;
          if (count == clk_freq_hz-1) begin
         pps_o <= !pps_o;
         count <= 0;
          end
       end

    endmodule

Before testing this in hardware we should run a simulation. Therefore we need a testbench. Testbenches usually follow the convension of ``modulename_tb.v``. In our case we will add the following code to ``pps_tb.v`` within the gpsemulator core directly, next to the ``pps.v`` that we created before. This will serve as our initial tetsbench. We will gradually improve the design of the testbench to showcase some FuseSoC features.

.. code:: verilog

    `timescale 1ns/1ns
    module pps_tb;

       parameter clk_freq_hz = 50_000;
       localparam clk_half_period = 1000_000_000/clk_freq_hz/2;

       reg clk = 1'b1;

       always #clk_half_period clk <= !clk;


       wire pps;

       pps
         #(.clk_freq_hz (clk_freq_hz))
       dut
         (.clk   (clk),
          .pps_o (pps));

       integer i;
       time last_edge = 0;

       initial begin
          @(pps);
          last_edge = $time;
          for (i=0; i<10;i=i+1) begin
         @(pps);
         if (($time-last_edge) != 1_000_000_000) begin
            $display("Error! Length of pulse was %0d ns", $time-last_edge);
            $finish;
         end else
           $display("Pulse %0d/10 OK!", i+1);
         last_edge = $time;
          end
          $display("Testbench finished OK");
          $finish;
       end

    endmodule

The code will create a 50MHz clock and check that the pps pulse changes every second (1,000,000,000 ns) for ten pulses. Also note that as the testbench will take forever to execute with a simulated 50MHz clock, we have changed the default clock frequency to 50KHz for now. Save it as pps\_tb.v in the core directory.

In order to let FuseSoC run a simulation, we need to add the files to our ``.core`` file. As ``pps.v`` and ``pps_tb.v`` have different purposes, with one being the RTL code and one being a testbench we will put them in different filesets. At this point it's not really necessary, but it will become apparent later why we choose to do this. Also note that the names of the filesets have no meaning. Just choose names that describe the intent. Add the following snippet to the .core file to create two new filesets.

.. code:: yaml

    filesets:
      rtl:
        files:
          - pps.v : {file_type : verilogSource}

      tb:
        files:
          - pps_tb.v : {file_type : verilogSource}

Next, we need to create a target that uses the filesets and also tell the simulation tool which module is our toplevel. We will use ``sim`` (for simulation) as the name of the target. Target names can also be chosen mostly arbitrarily, but there are some rules that we will come back to later. This snippet will set up our new target

.. code:: yaml

    targets:
      sim:
        filesets : [rtl, tb]
        toplevel: [pps_tb]

With the complete core file looking like

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
        filesets : [rtl, tb]
        toplevel: [pps_tb]

we are ready to go. Run ``fusesoc run --target=sim --tool=icarus blinky`` to build the simulation model and run it with Icarus Verilog.

In the next tutorial we will start experimenting with the options at our disposal to learn about some more FuseSoC features.
