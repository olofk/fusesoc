# Copyright FuseSoC contributors
# Licensed under the 2-Clause BSD License, see LICENSE for details.
# SPDX-License-Identifier: BSD-2-Clause

# FIXME: Fix nicer method to read JSON schema

capi2_schema = """
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CAPI2",
  "description": "Core API Version 2",
  "type": "object",
  "patternProperties": {
    "^name$": {
      "description": "VLNV identifier for core",
      "type": "string",
      "minProperties" : 1,
      "maxProperties" : 1
    },
    "^description$": {
      "description": "Short description of core",
      "type": "string"
    },
    "^provider$": {
      "description": "Provider of core",
      "type": "object",
      "anyOf": [
        {
          "description": "github Provider",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "pattern": "^github$"
            },
            "user": {
              "type": "string"
            },
            "repo": {
              "type": "string"
            },
            "version": {
              "type": "string"
            },
            "patches": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cachable": {
              "type": "boolean"
            }
          },
          "additionalProperties": false,
          "required": [
            "name",
            "user",
            "repo",
            "version"
          ]
        },
        {
          "description": "local Provider",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "pattern": "^local$"
            },
            "patches": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cachable": {
              "type": "boolean"
            }
          },
          "additionalProperties": false,
          "required": [
            "name"
          ]
        },
        {
          "description": "git Provider",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "pattern": "^git$"
            },
            "repo": {
              "type": "string"
            },
            "version": {
              "type": "string"
            },
            "patches": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cachable": {
              "type": "boolean"
            }
          },
          "additionalProperties": false,
          "required": [
            "name",
            "repo"
          ]
        },
        {
          "description": "opencores Provider",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "pattern": "^opencores$"
            },
            "repo_name": {
              "type": "string"
            },
            "repo_root": {
              "type": "string"
            },
            "revision": {
              "type": "string"
            },
            "patches": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cachable": {
              "type": "boolean"
            }
          },
          "additionalProperties": false,
          "required": [
            "name",
            "repo_name",
            "repo_root",
            "revision"
          ]
        },
        {
          "description": "url Provider",
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "pattern": "^url$"
            },
            "url": {
              "type": "string"
            },
            "user-agent": {
              "type": "string"
            },
            "verify_cert": {
              "type": "string"
            },
            "filetype": {
              "type": "string"
            },
            "patches": {
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "cachable": {
              "type": "boolean"
            }
          },
          "additionalProperties": false,
          "required": [
            "name",
            "url",
            "filetype"
          ]
        }
      ]
    },
    "^filesets$": {
      "description": "A fileset represents a group of files with a common purpose. Each file in the fileset is required to have a file type and is allowed to have a logical_name which can be set for the whole fileset or individually for each file. A fileset can also have dependencies on other cores, specified in the depend section",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "description": "Name of fileset",
          "type": "object",
          "patternProperties": {
            "^file_type$": {
              "description": "Default file_type for files in fileset",
              "type": "string"
            },
            "^logical_name$": {
              "description": "Default logical_name (i.e. library) for files in fileset",
              "type": "string"
            },
            "^tags$": {
              "description": "Default tags for files in fileset",
               "type": "array",
               "items": {
                 "type": "string"
               }
            },
            "^files(_append)?$": {
              "description": "Files in fileset",
              "type": "array",
              "minContains": 1,
              "items": {
                "oneOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "object",
                    "minProperties": 1,
                    "maxProperties": 1,
                    "patternProperties": {
                      "^.+$": {
                        "description": "Path to file",
                        "type": "object",
                        "properties": {
                          "define": {
                            "description": "Defines to be used for this file. These defines will be added to those specified in the target parameters section. If a define is specified both here and in the target parameter section, the value specified here will take precedence.  The parameter default value can be set here with ``param=value``",
                            "type": "object",
                            "patternProperties": {
                              "^.+$": {
                                "anyOf": [
                                  {
                                    "type": "string"
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  },
                                ]
                              }
                            }
                          },
                          "is_include_file": {
                            "description": "Treats file as an include file when true",
                            "type": "boolean"
                          },
                          "include_path": {
                            "description": "Explicitly set an include directory, relative to core root, instead of the directory containing the file",
                            "type": "string"
                          },
                          "file_type": {
                            "description": "File type. Overrides the file_type set on the containing fileset",
                            "type": "string"
                          },
                          "logical_name": {
                            "description": "Logical name, i.e. library for VHDL/SystemVerilog. Overrides the logical_name set on the containing fileset",
                            "type": "string"
                          },
                          "tags": {
                            "description": "Tags, special file-specific hints for the backends. Appends the tags set on the containing fileset",
                            "type": "array",
                            "items": {
                              "type": "string"
                            }
                          },
                          "copyto": {
                            "description": "Copy the source file to this path in the work directory",
                            "type": "string"
                          }
                        },
                        "additionalProperties": false
                      }
                    },
                    "additionalProperties": false
                  }
                ]
              }
            },
            "^depend(_append)?$": {
              "description": "Dependencies of fileset",
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          },
          "additionalProperties": false
        }
      },
      "additionalProperties": false
    },
    "^generate$": {
      "description": "The elements in this section each describe a parameterized instance of a generator. They specify which generator to invoke and any generator-specific parameters",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "description": "Name of generator to use",
          "properties": {
            "generator": {
              "description": "The generator to use. Note that the generator must be present in the dependencies of the core.",
              "type": "string"
            },
            "position": {
              "description": "Where to insert the generated core. Legal values are *first*, *prepend*, *append* or *last*. *prepend* (*append*) will insert core before (after) the core that called the generator",
              "type": "string",
              "pattern": "^first|prepend|append|last$"
            },
            "parameters": {
              "description": "Generator-specific parameters. ``fusesoc gen show $generator`` might show available parameters. ",
              "type": "object"
            }
          },
          "additionalProperties": false,
          "required": [
            "generator"
          ]
        }
      }
    },
    "^generators$": {
      "description": "Generators are custom programs that generate FuseSoC cores. They are generally used during the build process, but can be used stand-alone too. This section allows a core to register a generator that can be used by other cores.",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "description": "Name of generator",
          "properties": {
            "command": {
              "description": "The command to run (relative to the core root)",
              "type": "string"
            },
            "interpreter": {
              "description": "If the command needs a custom interpreter (such as python) this will be inserted as the first argument before command when calling the generator. The interpreter needs to be on the system PATH; specifically, shutil.which needs to be able to find the interpreter).",
              "type": "string"
            },
            "cache_type": {
              "description": "If the result of the generator should be considered cacheable. Legal values are *none*, *input* or *generator*.",
              "type": "string",
              "pattern": "^none|input|generator$"
            },
            "file_input_parameters": {
              "description": "All parameters that are file inputs to the generator. This option can be used when *cache_type* is set to *input* if fusesoc should track if these files change.",
              "type": "string"
            },
            "description": {
              "description": "Short description of the generator, as shown with ``fusesoc gen list``",
              "type": "string"
            },
            "usage": {
              "description": "A longer description of how to use the generator, including which parameters it uses (as shown with ``fusesoc gen show $generator``)",
              "type": "string"
            }
          },
          "additionalProperties": false,
          "required": [
            "command"
          ]
        }
      }
    },
    "^scripts$": {
      "description": "A script specifies how to run an external command that is called by the hooks section together with the actual files needed to run the script. Scripts are alway executed from the work root",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "patternProperties": {
            "^cmd(_append)?$": {
              "description": "List of command-line arguments",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^filesets(_append)?$": {
              "description": "Filesets needed to run the script",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^env$": {
              "description": "Map of environment variables to set before launching the script",
              "type": "object",
              "patternProperties": {
                "^.+$": {
                  "type": "string"
                }
              }
            }
          },
          "additionalProperties": false
        }
      }
    },
    "^targets$": {
      "description": "A target is the entry point to a core. It describes a single use-case and what resources that are needed from the core such as file sets, generators, parameters and specific tool options. A core can have multiple targets, e.g. for simulation, synthesis or when used as a dependency for another core. When a core is used, only a single target is active. The *default* target is a special target that is always used when the core is being used as a dependency for another core or when no ``--target=`` flag is set.",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "patternProperties": {
            "^default_tool$": {
              "description": "Default tool to use unless overridden with ``--tool=`` This key is used by the Edalize Tool API and is ignored if the Flow API is used instead.",
              "type": "string"
            },
            "^description$": {
              "description": "Description of the target",
              "type": "string"
            },
            "^flow$": {
              "description": "Edalize backend flow to use for target. Setting this key enables the flow API instead of the legacy Tool API.",
              "type": "string"
            },
            "^flow_options$": {
              "description": "Tool- and flow-specific options. Used by the Flow API. The Edalize documentation contains information on available options for different flows (https://edalize.readthedocs.io/en/latest/edam/api.html#flow-options)",
              "type": "object",
              "patternProperties": {
                "^.+$": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "number"
                    },
                    {
                      "type": "boolean"
                    },
                    {
                      "type": "array"
                    },
                    {
                      "type": "object"
                    }
                  ]
                }
              }
            },
            "^hooks$": {
              "description": "Script hooks to run when target is used",
              "type": "object",
              "patternProperties": {
                "^pre_build(_append)?$": {
                  "description": "Scripts executed before the *build* phase",
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "^post_build(_append)?$": {
                  "description": "Scripts executed after the *build* phase",
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "^pre_run(_append)?$": {
                  "description": "Scrips executed before the *run* phase",
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                },
                "^post_run(_append)?$": {
                  "description": "Scripts executed after the *run* phase",
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              },
              "additionalProperties": false
            },
            "^tools$": {
              "description": "Tool-specific options for target. Used by the legacy Tool API. The contents of this section is handled by Edalize, and a list of available tool options for each tool can be found in the Edalize documentation (https://edalize.readthedocs.io/en/latest/edam/api.html#tool-options)",
              "type": "object",
              "patternProperties": {
                "^.+$": {
                  "type": "object",
                  "patternProperties": {
                    "^.+$": {
                      "anyOf": [
                        {
                          "type": "string"
                        },
                        {
                          "type": "number"
                        },
                        {
                          "type": "boolean"
                        },
                        {
                          "type": "array"
                        },
                        {
                          "type": "object"
                        }
                      ]
                    }
                  }
                }
              }
            },
            "^toplevel$": {
              "description": "Top-level module. Normally a single module/entity but can be a list of several items",
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "array",
                  "items": {
                    "type": "string"
                  }
                }
              ]
            },
            "^filesets(_append)?$": {
              "description": "File sets to use in target",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^filters(_append)?$": {
              "description": "EDAM filters to apply",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^generate(_append)?$": {
              "description": "Parameterized generators to run for this target with optional parametrization",
              "type": "array",
              "items": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "object"
                  }
                ]
              }
            },
            "^parameters(_append)?$": {
              "description": "Parameters to use in target. The parameter default value can be set here with ``param=value``",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^vpi(_append)?$": {
              "description": "VPI modules to build and include for target",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "flags": {
              "description": "Default values of flags",
              "type": "object",
              "patternProperties": {
                "^.+$": {
                  "anyOf": [
                    {
                      "type": "string"
                    },
                    {
                      "type": "number"
                    },
                    {
                      "type": "boolean"
                    },
                    {
                      "type": "array"
                    },
                    {
                      "type": "object"
                    }
                  ]
                }
              }
            }
          },
          "additionalProperties": false
        }
      }
    },
    "^parameters$": {
      "description": "Available parameters",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "properties": {
            "datatype": {
              "description": "Parameter datatype. Legal values are *bool*, *file*, *int*, *str*. *file* is same as *str*, but prefixed with the current directory that FuseSoC runs from",
              "type": "string",
              "pattern": "^bool|file|int|real|str$"
            },
            "default": {
              "description": "Default value",
              "oneOf": [
                {
                  "type": "boolean"
                },
                {
                  "type": "string"
                },
                {
                  "type": "number"
                }
              ]
            },
            "description": {
              "description": "Description of the parameter, as can be seen with ``fusesoc run --target=$target $core --help``",
              "type": "string"
            },
            "paramtype": {
              "description": "Specifies type of parameter. Legal values are *cmdlinearg* for command-line arguments directly added when running the core, *generic* for VHDL generics, *plusarg* for verilog plusargs, *vlogdefine* for Verilog `` `define`` or *vlogparam* for verilog top-level parameters. All paramtypes are not valid for every backend. Consult the backend documentation for details.",
              "type": "string"
            },
            "scope": {
              "description": "**Not used** : Kept for backwards compatibility",
              "type": "string"
            }
          },
          "additionalProperties": false,
          "required": [
            "datatype",
            "paramtype"
          ]
        }
      }
    },
    "^vpi$": {
      "description": "A VPI (Verilog Procedural Interface) library is a shared object that is built and loaded by a simulator to provide extra Verilog system calls. This section describes what files and external libraries to use for building a VPI library",
      "type": "object",
      "patternProperties": {
        "^.+$": {
          "patternProperties": {
            "^filesets(_append)?$": {
              "description": "Filesets containing files to use when compiling the VPI library",
              "type": "array",
              "items": {
                "type": "string"
              }
            },
            "^libs(_append)?$": {
              "description": "External libraries to link against",
              "type": "array",
              "items": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "^virtual(_append)?$": {
      "description": "VLNV of a virtual core provided by this core. Versions are currently not supported, only the VLN part is used.",
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  },
  "additionalProperties": false
}
"""
