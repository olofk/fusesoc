# FuseSOC: Dependencies

Even if the simulations seem to work fine it's often very useful to look at the waveform from our simulation to verify that the testbench works as intended.

Running `fusesoc run --target=sim --tool=icarus blinky --help` will not reveal any options for doing waveform dumps. We will now fix that, but instead of adding the code for creating waveforms ourselves to the test bench, we will take advantage of a core called vlog_tb_utils from the FuseSoC standard library which does that and more.

To do that, we need to add a dependency on vlog_tb_utils. Dependencies in FuseSoC are tied to filesets, so we need to add a dependency from the fileset that will use vlog_tb_utils, which is the `tb` fileset in this case. Change the fileset to look like this:

  tb:
    files:
      - pps_tb.v : {file_type : verilogSource}
    depend: [vlog_tb_utils]

The `depend` section is a list of VLNV entries we want to depend on. In the most basic form it will depend on the latest version of vlog_tb_utils. Running `fusesoc list-cores` will show all the available versions of each core. If we want to use a specific version of a core, we can add a version modifier, such as ">=vlog_tb_utils-1.1", "<vlog_tb_utils-1.1" or "=vlog_tb_utils-1.0". Specifying an exact version of a core is generally discouraged if other versions work too, as there will be conflicts when resolving dependencies if one core depends on =vlog_tb_utils-1.0 while another depends on =vlog_tb_utils-1.1. If those are the minimum versions required, it's instead better to depend on >=vlog_tb_utils-1.0 and >=vlog_tb_utils-1.1 since it will allow FuseSoC to find a version (1.1) that works for both cases. Some other rules regarding version and name matching to be aware of:

* core_name is a short-hand notation for the VLNV identifier ::core_name
* core_name will depend on the latest version of the core
* core_name-version will depend on that exact version. If using VLNV names, the syntax is instead ::core_name:version
* The version modifiers are <,<=,=,>,>=
* Due to yaml parsing, using version modifiers require the whole string to be quoted, e.g. ">=core_name-version"

We can now run `fusesoc run --target=sim --tool=icarus blinky --help` to see some new options available.

Just adding the core as a dependency doesn't do much difference though. We also need to make use of it. vlog_tb_utils exposes a module called vlog_tb_utils that we will now add to the testbench.

Add the following line to the testbench to instantiate the helper module.

   vlog_tb_utils vtu();

Running `fusesoc run --target=sim blinky --vcd` will now create a file called estlog.vcd` in `build/blinky_0/sim-icarus`.

Feel free to try all the target-specific options with different tools, but beware that some of the options won't do anything at this point and other will behave very differently between tools. We will return to that later, but our next task will be to introduce parameters before we can finally see our code running on real hardware. Until then, our core file should look like this

```yaml
CAPI=2:
name : ::blinky:0

filesets:
  rtl:
    files:
      - pps.v : {file_type : verilogSource}

  tb:
    files:
      - pps_tb.v : {file_type : verilogSource}
    depend: [vlog_tb_utils]

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
```
