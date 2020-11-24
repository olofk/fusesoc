.. _ref_gapi:

**************
GAPI Reference
**************

:term:`GAPI` is the file format used to pass configuration data between FuseSoC and a generator.
It is based on :term:`YAML` with the following schema.

========== ===========
Key        Description
========== ===========
gapi       Version of the generator configuration file API. Only 1.0 is defined
files_root Directory where input files are found. FuseSoC sets this to the calling core's file directory
vlnv       Colon-separated VLNV identifier to use for the output core. A generator is free to ignore this and use another VLNV.
parameters Everything contained under the parameters key should be treated as instance-specific configuration for the generator
========== ===========
