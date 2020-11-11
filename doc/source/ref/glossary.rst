********
Glossary
********

In the context of FuseSoC some terms have special meaning.
This glossary section explains some of the jargon used.

.. glossary::
   :sorted:

   core
      A core is a reasonably self-contained, reusable piece of IP, such as a FIFO implementation.
      See also :ref:`ug_overview_cores`.

   core file
   core description file
      A file describing a :term:`core`, including source files, available targets, etc.

   semantic versioning
   SemVer
      Semantic versioning is a convention to give meaning to version numbers.
      See :ref:`ug_build_system_dependencies_semver` and `semver.org <semver.org>`_.

   target
      See :ref:`ug_overview_targets`.

   tool
   tool flow
      See :ref:`ug_overview_toolflows`.

   stage
   build stage
      See :ref:`ug_overview_buildstages`.

   YAML
      YAML is (among other things) a markup language, commonly used for configuration files.
      It is used in FuseSoC in various places, especially for :term:`core description files <core file>` and for EDAM files.

      Read more about YAML on `Wikipedia <https://en.wikipedia.org/wiki/YAML>`_ or on `yaml.org <https://yaml.org/>`_.

   VLNV
      Vendor, Library, Name, and Version: the format used for :term:`core` names.
      In core names, the four parts are separated by colons, forming a name like ``vendor:library:name:version``.

      See also :ref:`ug_build_system_core_name`.
