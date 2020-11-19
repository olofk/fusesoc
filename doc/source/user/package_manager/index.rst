***************************
The FuseSoC package manager
***************************

.. todo::

   This section of the documentation is copied over from previous documentation and needs to be edited in style and extended.

Core libraries
---------------

A collection of one or more cores in a directory tree is called a core
library. FuseSoC supports working with multiple core libraries. The
locations of the libraries are specified in the FuseSoC configuration
file, ``fusesoc.conf``

To find a configuration file, FuseSoC will first look for
``fusesoc.conf`` in the current directory, and if there is no file
there, it will search next in ``$XDG_CONFIG_HOME/fusesoc`` (i.e.
``~/.config/fusesoc`` on Linux and ``%HOMEPATH%\.config\fusesoc`` on
Windows) and lastly in ``/etc/fusesoc``

By running ``fusesoc init`` after FuseSoC is installed, the standard
libraries will be installed, and a default configuration file will be
created in ``$XDG_CONFIG_HOME/fusesoc/fusesoc.conf`` on Linux and ``%HOMEPATH%\.config\fusesoc\fusesoc.conf`` on
Windows with the following
contents:

::

   [library.orpsoc-cores]
   sync-uri = https://github.com/openrisc/orpsoc-cores
   sync-type = git

   [library.fusesoc-cores]
   sync-uri = https://github.com/fusesoc/fusesoc-cores
   sync-type = git

Core search order
-----------------

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
