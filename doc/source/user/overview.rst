FuseSoC
=======

FuseSoC is a package manager and a set of build tools for HDL code.

Its main purpose is to increase reuse of IP cores and be an aid for creating,
building and simulating SoC solutions.

Core description files
----------------------

capi (Core API) is the format for core description files. Current version is
version 2.0. A capi 2.0 file is identified by the string “CAPI=2” in the
beginning of a file. The rest of the file is a standard YAML_ file.

Core naming rules
-----------------

FuseSoC uses ``VLNV`` tags to uniquely identify a core. ``VLNV`` is a concept
borrowed from the IP-XACT and stands for Vendor Library Name Version. This means
that the name of the cores consists of four parts, which are generally separated
by ‘:’, such as ``librecores.org:peripherals:uart16550:1.5``. In FuseSoC, it is
allowed to leave out all parts of the VLNV tag except for the name part, e.g
``::uart16550``. In those cases, the Vendor and Library parts will be empty
strings, and the version will be set to 0.

As the VLNV concept was introduced in FuseSoC after many core files had already
been created, FuseSoC still supports parsing files with the legacy naming
convention. These can either be of the format ``name``, in which case they will
be translated internally to VLNV tags with the Name field set, and Version set
to 0, or they can be of the format ``name-version``, which will also set the
Version field.

As an extension to the VLNV naming scheme, FuseSoC also support specifying a
revision of a core file. This is a fifth field that can be added to both legacy
and VLNV names by adding ``-r<revision>`` as a suffix (e.g.
``::uart16550:1.5-r1``, ``uart16550-1.5-r1``, ``uart16550-r1``). This is used to
make updates to the ``.core`` file even if the source of the core is unchanged.

Core libraries
---------------

A collection of one or more cores in a directory tree is called a core
library. FuseSoC supports working with multiple core libraries. The
locations of the libraries are specified in the FuseSoC configuration
file, ``fusesoc.conf``

To find a configuration file, FuseSoC will first look for
``fusesoc.conf`` in the current directory, and if there is no file
there, it will search next in ``$XDG_CONFIG_HOME/fusesoc`` (i.e.
``~/.config/fusesoc`` on Linux and ``%LOCALAPPDATA%\fusesoc`` in
Windows) and lastly in ``/etc/fusesoc``

By running ``fusesoc init`` after FuseSoC is installed, the standard
libraries will be installed, and a default configuration file will be
created in ``$XDG_CONFIG_HOME/fusesoc/fusesoc.conf`` with the following
contents:

::

   [library.orpsoc-cores]
   sync-uri = https://github.com/openrisc/orpsoc-cores
   sync-type = git

   [library.fusesoc-cores]
   sync-uri = https://github.com/fusesoc/fusesoc-cores
   sync-type = git

Core search order
------------------

Once FuseSoC has found its configuration file, it will parse the
``cores_root`` option in the ``[main]`` section of ``fusesoc.conf``.
This option is a space-separated list of library locations which are
searched in the order they appear. Additional library locations can be
added on the command line by setting the ``--cores-root`` parameter when
FuseSoC is launched. The library locations specified from the
command-line will be parsed after those in ``fusesoc.conf``

For each library location, FuseSoC will recursively search for files
with a *.core* suffix. Each of these files will be parsed and addded to
the in-memory FuseSoC database if they are valid ``.core`` files.

Several ``.core`` files can reside in the same directory and they will all be parsed.

If several cores with the same VLNV identifier are encountered the latter will
replace the former. This can be used to override cores in a library with an
alternative core in another library by specifying them in a library that will be
parsed later, either temporarily by adding ``--cores-root`` to the command-line,
or permanently by adding the other library at the end of fusesoc.conf

Making changes to cores in a library
-------------------------------------
A common situation is that a user wants to use their own copy of a core,
instead of the one provided by a library, for example to fix a bug or
add new functionality. The following steps can be used to achieve this:

**Example.** Replace a core in a library with a user-specified version

#. Create a new directory to keep the user-copies of the cores (this
   directory will be referred to as ``$corelib`` from now on)
#. Download the core source (the repository or URL can be found in the
   ``[provider]`` section of the original core)
#. *If the downloaded core already contains a .core file, this step is
   ignored* Copy the original .core file to the root of the downloaded
   core. Edit the file and remove the ``[provider]`` section. (This will
   stop FuseSoC from downloading the core and use files from the
   directory containing the .core file instead)
#. Add ``$corelib`` to the end of your library search path, either by
   editing ``fusesoc.conf`` or by adding ``--cores-root=$corelib`` to
   the command-line arguments
#. Verify that the new core is found by running fusesoc core-info $core. Check
   the output to see that “Core root:” is set to the directory where the core
   was downloaded

Backends
--------

FuseSoC uses the backends available from edalize_.

Migration guide
---------------

As new features are added to FuseSoC, some older features become obsolete. Read
the link:migrations{outfilesuffix}[migration guide] to learn how to keep the
.core files up-to-date with the latest best practices

.. _YAML: https://yaml.org
.. _configparser: http://docs.python.org/2/library/configparser.html
.. _edalize: https://github.com/olofk/edalize
