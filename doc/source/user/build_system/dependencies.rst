.. _ug_build_system_dependencies:

Dependencies: link cores together for re-use
============================================

For a long time, productivity gains in hardware designs have been achieved primarily by re-using existing code, a.k.a. IP blocks.
Re-use is also engrained into FuseSoC: re-usable hardware design components are packaged into cores and then used in other designs.
In FuseSoC (and many other package managers), re-use is achieved by expressing dependencies between FuseSoC cores.

This section explains how dependencies are specified, how they are resolved by FuseSoC, and how they can be constrained.

A dependency example: DualBlinky
--------------------------------

We introduced the basic FuseSoC features by creating an reusable core called Blinky.
To illustrate the concept of dependencies in FuseSoC we employ another example: DualBlinky, the "dual-core" version of Blinky.
Again, all source code is available in the `FuseSoC source tree <https://github.com/olofk/fusesoc>`_ in the ``tests/userguide/dualblinky`` directory.

.. code-block:: console

   $ tree tests/userguide/dualblinky
   tests/userguide/dualblinky
   ├── data
   │   └── nexys_video.xdc
   ├── dualblinky.core
   └── rtl
      └── dualblinky.sv

   2 directories, 3 files

The core file is shown in full below.

.. literalinclude:: ../../../../tests/userguide/dualblinky/dualblinky.core
   :language: yaml
   :caption: ``dualblinky.core``, 2x Blinky
   :name: ug_build_system_cb_dualblinky_full


Specifying a dependency
-----------------------

Dependencies in FuseSoC are expressed between a file set and a core.
They are listed in a :term:`core file` as in the ``filesets.FILESET_NAME.depend`` section.

The example below shows how to create a dependency between the ``fusesoc:examples:blinky`` core and the ``rtl`` file set of the ``fusesoc:examples:dualblinky:1.0`` core.

.. code-block:: yaml

   # Excerpt of dualblinky.core

   # ...

   filesets:
     # ...
     rtl:
       # ...
       depend:
         - ">=fusesoc:examples:blinky:1.0"

.. note::

   YAML requires quotation marks for strings with special characters, as they are used in version constraints.
   Both single (``'``) and double quotes (``"``) can be used.


File ordering
-------------

File ordering (compilation order) is important in many hardware design projects.
The following rules apply.

* Files from dependencies are inserted into the file list before the files in the file set where the dependency is declared.
* The order in which dependencies are listed in the ``depend`` section does not imply any ordering.
  That is, specifiying ``depend: [A, B]`` does not guarantee that files from core ``A`` are included before the ones from core ``B``.
  (If such an order is desired, make core ``B`` depend on ``A``.)

What happens if a dependency is specified?
------------------------------------------

Declaring a dependency includes the dependent core in the build.
More specificially, the following sections specified in the ``default`` target of the dependent core are included:

* ``filesets``: File sets to include.
* ``hooks``: A list of hooks to execute.
* ``generate``: List of generators.
* ``parameters``: List of available parameters.
* ``vpi``: List of VPI objects.

Notably *not* included are the ``tools``, ``toplevel``, ``description``, and ``default_tool`` sections of the ``default`` target.
Also, no target other than ``default`` is considered when including a dependency.

Version constraints
-------------------

Version constraints specify which version of a dependent core can be used, and which versions are incompatible.

Within a :term:`core file`, version constraints are expressed by prefixing a core name with a version comparision operator.
The following version comparison operators are available.

.. list-table:: Version comparison operators
   :widths: 10 40 50
   :header-rows: 1

   * - Operator
     - Meaning
     - Example
   * - ``=``
     - exactly
     - ``=fusesoc:examples:blinky:1.2``: exactly version 1.2
   * - ``<``
     - less (lower) than
     - ``<fusesoc:examples:blinky:1.2``: any version before 1.2, e.g. 0.9
   * - ``<=``
     - at most (less than or equal to)
     - ``<=fusesoc:examples:blinky:1.2``: at most version 1.2, e.g. 0.9, or 1.2
   * - ``>=``
     - at least (greater than or equal to)
     - ``>=fusesoc:examples:blinky:1.2``: version 1.2, or any newer version, e.g. 1.2, or 10.7
   * - ``>``
     - more (higher) than
     - ``>fusesoc:examples:blinky:1.2``: any version after 1.2, e.g. 1.3, or 10.7
   * - ``^``
     - Caret requirement: any version less than the next major version (see below)
     - ``^fusesoc:examples:blinky:1.2``: >=1.2.0 <1.3.0
   * - ``~``
     - Tilde requirement: allow updates to the current version (see below)
     - ``~fusesoc:examples:blinky:1.2``: >=1.2.0 <2.0.0

Notes:

* If no operator is specified, then ``=`` is assumed.
  So the ``=`` operator is effectively optional.
* If no version number is given any version is accepted, i.e. ``>= 0.0.0``.

Caret requirements
~~~~~~~~~~~~~~~~~~

Caret requirements allow semantic versioning-compatible updates to a specified version.
An update is allowed if the new version number does not modify the left-most non-zero digit in the major, minor, patch grouping.

Tilde requirements
~~~~~~~~~~~~~~~~~~

Tilde requirements specify a minimal version with some ability to update.
If you specify a major, minor, and patch version or only a major and minor version, only patch-level changes are allowed.
If you only specify a major version, then minor- and patch-level changes are allowed.

.. _ug_build_system_dependencies_semver:

Semantic versioning (SemVer)
----------------------------

A common scenario when declaring dependency is the following: "Core B depends on a version of core A which has the same interface as version 1.0.0, but may contain additional bug fixes in the implementation of that interface."
Version numbers and dependencies alone cannot express this relationship, as they are (by default) meaningless.
Equally, tools have a very hard time determining such compatibility accurately.
Instead, humans are needed to attach meaning to version numbers, and that's where semantic versioning comes in.

Semantic versioning is a convention that gives meaning to version numbers.
Being a convention, semantic versioning is not enforced by tooling, but relies on cooperation and a shared understanding between authors of reusable IP cores.
Effectively, semantic versioning allows authors to encode in the version number information such as "this version breaks API compatibility", "this version is backwards compatible with a certain previous version", etc.

A detailed explanation of semantic versioning is available at `semver.org <https://semver.org/>`_.
The basics, however, are quickly explained.
Semantic versioning expects version numbers with three components, MAJOR, MINOR, and PATCH, such as 1.0.3.
With this structure in place, follow these guidelines:

.. epigraph::

   Given a version number MAJOR.MINOR.PATCH, increment the:

   #. MAJOR version when you make incompatible API changes,
   #. MINOR version when you add functionality in a backwards compatible manner, and
   #. PATCH version when you make backwards compatible bug fixes.

   Additional labels for pre-release and build metadata are available as extensions to the MAJOR.MINOR.PATCH format.

   -- `Semantic Versioning 2.0.0 (Summary) <https://semver.org/>`_
