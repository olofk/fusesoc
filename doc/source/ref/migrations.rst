***************
Migration guide
***************

FuseSoC strives to be backwards-compatible, but as new features are added to FuseSoC, some older features become obsolete.
This chapter contains information on how to migrate away from deprecated features to keep the core description files up-to-date with the latest best practices.

Migrating from CAPI1 to CAPI2
=============================

Why
---

FuseSoC's `.core` files are written in a "language" called CAPI.
The current version of CAPI is version 2, also called CAPI2.
Going forward, only the newer CAPI2 file format will be supported, which simplifies the use and implementation of FuseSoC greatly.

When
----

In FuseSoC 1.x, both CAPI1 and CAPI2 are supported.
Starting with FuseSoC 2 only CAPI2 will be supported.
To be able to update to the next version of FuseSoC seamlessly you need to migrate your existing CAPI1 core files to CAPI2.
We recommend doing this migration *now* while still running FuseSoC 1.x.

How
---

FuseSoC ships with an automated conversion tool from CAPI1 to CAPI2, which provides a solid starting point for the conversion process.
However, even though CAPI2 supports almost all features of CAPI1, there isn't always a 1:1 mapping between the two formats.
Therefore the automatic conversion won't be always correct, and a bit of manual cleanup work will be needed.

To convert a single core file, follow these steps:

1. Ensure you're running the latest version of FuseSoC 1.x.
2. Ensure that you have a backup of your core file, or have committed the current version in a version control system.
3. Run ``fusesoc migrate-capi1-to-capi2 --inplace your_core_file.core`` to convert the file automatically.
4. Open ``your_core_file.core`` to check the conversion output and adjust it as necessary (e.g. add back comments, adjust the ordering of statements, etc.)

You can find documentation on the :ref:`CAPI1 <ref_capi1>` as well as on :ref:`CAPI2 <ref_capi2>` in the reference manual.
We also recommend to have a look at the :ref:`ug_build_system_core_files` section in the user guide for current best practices on writing CAPI2 core files.

To convert all core files in a directory, Linux users can run the following command:

.. code-block::

   find your_coredir -iname '*.core' -exec fusesoc migrate-capi1-to-capi2 --nowarn --inplace {} \;

If you get stuck in the conversion process, or if a CAPI1 feature you rely on isn't available in CAPI2, please get in touch by `filing an issue on GitHub <https://github.com/olofk/fusesoc/issues/new>`_.

Migrating from .system files
============================

Why
---

The synthesis backends required a separate .system file in addition to
the .core file. There is however very little information in the .system
file, it was never properly documented and some information is
duplicated from the .core file. For these reasons a decision was made to
drop the .system file and move the relevant information to the .core
file instead.

When
----

``.system`` files are no longer needed as of FuseSoC 1.6

The ``.system`` file will still be supported for some time to allow
users to perform the migration, but any equivalent options in the
``.core`` file will override the ones in ``.system``

How
---

Perform the following steps to migrate from .system files

1. Move the ``backend`` parameter from the ``main`` section in the
   ``.system`` file to the ``main`` section in the ``.core`` file

2. Move the backend section (i.e. ``icestorm``, ``ise``, ``quartus`` or
   ``vivado``) to the ``.core`` file

3. Move ``pre_build_scripts`` from the ``scripts`` section in the
   ``.system`` file to ``pre_synth_scripts`` in the ``scripts`` section
   in the ``.core`` file.

4. Move ``post_build_scripts`` from the ``scripts`` section in the
   ``.system`` file to ``post_impl_scripts`` in the ``scripts`` section
   in the ``.core`` file.

Migrating from plusargs
=======================

Why
---

Up until FuseSoC 1.3, verilog plusargs were the only way to set
external run-time parameters. Cores could register which plusargs they
supported through the ``plusargs`` section. This mechanism turned out to
be too limited, and in order to support public/private parameters,
defines, VHDL generics etc, ``parameter`` sections were introduced to
replace the ``plusargs`` section.

When
----

``parameter`` sections were introduced in FuseSoC 1.3

The ``plusargs`` section is still supported to allow time for migrations

How
---

Entries in the ``plusargs`` section are described as
``<name> = <type> <description>``. For each of these entries, create a
new section with the following contents

::

   [parameter <name>]
   datatype = <type>
   description = <description>
   paramtype = plusarg

The ``parameter`` sections also support the additional tags ``default``,
to set a default value, and ``scope`` to select if this parameter should
be visible to other cores (``scope=public``) or only when this core is
used as the toplevel (``scope=private``).

Migrating to filesets
=====================

Why
---

Originally only verilog source files were supported. In order to
make source code handling more generic, filesets were introduced.
Filesets are modeled after IP-XACT filesets and each fileset lists a
group of files with similar purpose. Apart from supporting more file
types, the filesets contain some additional control over when to use the
files. The verilog section is still supported for some time to allow
users to perform the migration.

When
----

``fileset`` sections were introduced in FuseSoC 1.4

The ``verilog`` section is still supported to allow time for migrations

How
---

Given a ``verilog`` section with the following contents:

::

   [verilog]
   src_files = file1.v file2.v
   include_files = file3.vh file4.vh
   tb_src_files = file5.v file6.v
   tb_include_files = file7.vh file8.vh
   tb_private_src_files = file9.v file10.v

these will be turned into multiple file sets. The names of the file sets
are not important, but should reflect the usage of the files.

::

   [fileset src_files]
   files = file1.v file2.v
   file_type = verilogSource

   [fileset include_files]
   files = file3.vh file4.vh
   file_type = verilogSource
   is_include_file = true

   [fileset tb_src_files]
   files = file5.v file6.v
   file_type = verilogSource
   usage = sim

   [fileset tb_include_files]
   files = file7.vh file8.vh
   file_type = verilogSource
   is_include_file = true
   usage = sim

   [fileset tb_private_src_files]
   files = file9.v file10.v
   file_type = verilogSource
   scope = private
   usage = sim

If not specified, ``usage = sim synth`` and ``scope = public``

These filesets can be further combined by setting some per-file
attributes

::

   [fileset src_files]
   files =
    file1.v
    file2.v
    file3.vh[is_include_file]
    file4.vh[is_include_file]
   file_type = verilogSource

   [fileset public_tb_files]
   files = file5.v file6.v file7.vh[is_include_file] file8.vh[is_include_file]
   file_type = verilogSource
   usage = sim

   [fileset tb_files]
   files = file9.v file10.v
   file_type = verilogSource
   scope = private
   usage = sim

``file_type`` can also be overridden on a per-file basis (e.g.
``file2.v[file_type=verilogSource-2005]``
``file3.vh[is_include_file,file_type=systemVerilogSource]``), but scope
and usage are set for each fileset.

Migrating from verilator define_files
=====================================

Why
---

Files specified as ``define_files`` in the verilator core
section were treated as verilog files containing ```define``
statements to C header files with equivalent #define statements. While
there are use-cases for this functionality, the actual implementation is
limited and makes assumptions that makes it difficult to maintain in the
FuseSoC code base. The decision is therefore made to deprecate this
functionality and instead require the user to make the conversion.

When
----

``verilator define_files`` are no longer converted in FuseSoC 1.7

How
---

The following stand-alone Python script will perform the same function.
It can also be executed as a ``pre_build`` script to perform the
conversion automatically before a build

::

   def convert_V2H( read_file, write_file):
       fV = open (read_file,'r')
       fC = open (write_file,'w')
       fC.write("//File auto-converted the Verilog to C. converted by FuseSoC//\n")
       fC.write("//source file --> " + read_file + "\n")
       for line in fV:
           Sline=line.split('`',1)
           if len(Sline) == 1:
               fC.write(Sline[0])
           else:
               fC.write(Sline[0]+"#"+Sline[1])
       fC.close
       fV.close

   import sys
   if __name__ == "__main__":
       convert_V2H(sys.argv[1], sys.argv[2])

Redefining build_root
=====================

Why
---
As an aid for scripts executed during the build process, a number of environment variables were defined. Unfortunately this was done without too much thought and as time moved on, some of these turned out to be a maintenance burden without bringing much benefit, and in some cases without ever being used.

At the same time, the introduction of VLNV and dependency ranges has introduced non-determinism in where the output of a build ends up. For these reasons, it was determined to redefine the rarely used `build_root` variable to point to the the directory containing the work root and exported files. A `--build-root` command-line switch is introduced to explictly set a build_root. Setting `build_root` in `fusesoc.conf` will keep working the same way as before, but the command-line switch takes precedence. CAPI1 cores will no longer export the `BUILD_ROOT` environment variable.

These changes affects the following cases:

* Relying on the `BUILD_ROOT` variable in scripts called from CAPI1 cores.

When
----
`build_root` was redefined after the release of FuseSoC 1.9.1

How
---
Any scripts that previously relied on ``$BUILD_ROOT`` will have to be updated. Note that due to other changes in FuseSoC most of them were unlikely to work at this point anyway.
