***************************
The FuseSoC package manager
***************************

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

By running ``fusesoc library add fusesoc_cores https://github.com/fusesoc/fusesoc-cores`` after FuseSoC is installed, the standard
libraries will be installed, and a default configuration file will be
created in ``$XDG_CONFIG_HOME/fusesoc/fusesoc.conf`` on Linux and ``%HOMEPATH%\.config\fusesoc\fusesoc.conf`` on
Windows with the following
contents:

::

   [library.fusesoc-cores]
   sync-uri = https://github.com/fusesoc/fusesoc-cores
   sync-type = git

Core search order
-----------------

Once FuseSoC has found its configuration file, it will parse the library sections in the order they appear in the file. Library sections are all sections named `library.<library name>`. The following keys are valid in the library sections.

location
~~~~~~~~
Specifies the library's location in the file system (required)

auto-sync
~~~~~~~~~
Boolean value specifying if the library should be automatically updated when running `fusesoc library update` (optional. defaults to `true`)

sync-uri
~~~~~~~~
The URI for non-local libraries where to fetch the library (optional)

sync-type
~~~~~~~~~
The type of library. Can be set to `git` or `local`. A missing value indicates a `local` library. (optional)

Additional library locations can be added on the command line by setting the ``--cores-root`` parameter when
FuseSoC is launched. The library locations specified from the
command-line will be parsed after those in ``fusesoc.conf``

For each library location, FuseSoC will recursively search for files
with a *.core* suffix. Each of these files will be parsed and added to
the in-memory FuseSoC database if they are valid ``.core`` files.

Several ``.core`` files can reside in the same directory and they will all be parsed.

If several cores with the same VLNV identifier are encountered the latter will
replace the former. This can be used to override cores in a library with an
alternative core in another library by specifying them in a library that will be
parsed later, either temporarily by adding ``--cores-root`` to the command-line,
or permanently by adding the other library at the end of fusesoc.conf

If FuseSoC encounters a file called `FUSESOC_IGNORE` in a directory, this directory and all subdirectories will be ignored.
