*****************************
Common Problems and Solutions
*****************************

Making changes to cores in a library
====================================

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
