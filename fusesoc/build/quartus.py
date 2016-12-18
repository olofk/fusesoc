import os.path
import shutil
import subprocess
from fusesoc import utils

from fusesoc.build.backend import Backend
class Quartus(Backend):

    MAKEFILE_TEMPLATE = """

all: sta

project: $(TCL_FILE)
	quartus_sh $(QUARTUS_OPTIONS) -t $(DESIGN_NAME).tcl

map: project
	quartus_map $(QUARTUS_OPTIONS) $(DESIGN_NAME)

fit: map
	quartus_fit $(QUARTUS_OPTIONS) $(DESIGN_NAME)

asm: fit
	quartus_asm $(QUARTUS_OPTIONS) $(DESIGN_NAME)

sta: asm
	quartus_sta $(QUARTUS_OPTIONS) $(DESIGN_NAME)

clean:
	rm -rf *.* db incremental_db
"""

    def configure(self, args):
        super(Quartus, self).configure(args)
        self._run_qsys()
        self._write_tcl_file()
        self._write_makefile()

    # Runs qsys if a 'qsys_files' entry can be found under the quartus section
    def _run_qsys(self):
        self.qip_files = []
        if not self.backend.qsys_files:
            return

        qsys_script = open(os.path.join(self.work_root, 'qsys.sh'), 'w')

        for f in self.backend.qsys_files:
            dst_file = os.path.join(self.work_root, f.name)
            dst_dir = os.path.dirname(dst_file)

            args = []
            args += ['--project-directory=' + dst_dir]
            args += ['--output-directory=' +
                     os.path.join(self.src_root, 'qsys')]
            args += ['--report-file=bsf:' +
                     os.path.join(dst_dir, self.system.sanitized_name+'.bsf')]
            args += ['--system-info=DEVICE_FAMILY=' +
                     self.backend.family]
            args += ['--system-info=DEVICE=' +
                     self.backend.device]
            args += ['--component-file=' + dst_file]

            qsys_script.write('ip-generate ' + ' '.join(args) + '\n')

            self.qip_files += [os.path.join(self.src_root,
                                            'qsys/synthesis',
                                            self.system.sanitized_name+'.qip')]
            args = []
            args += ['--project-directory=' + dst_dir]
            args += ['--output-directory=' +
                     os.path.join(self.src_root, 'qsys/synthesis')]
            args += ['--file-set=QUARTUS_SYNTH']
            args += ['--report-file=sopcinfo:' +
                     os.path.join(dst_dir, self.system.sanitized_name+'.sopcinfo')]
            args += ['--report-file=html:' +
                     os.path.join(dst_dir, self.system.sanitized_name+'.html')]
            args += ['--report-file=qip:' + self.qip_files[-1]]
            args += ['--report-file=cmp:' +
                     os.path.join(dst_dir, self.system.sanitized_name+'.cmp')]
            args += ['--report-file=svd']
            args += ['--system-info=DEVICE_FAMILY=' +
                     self.backend.family]
            args += ['--system-info=DEVICE=' +
                     self.backend.device]
            args += ['--component-file=' + dst_file]
            args += ['--language=VERILOG']

            qsys_script.write('ip-generate ' + ' '.join(args) + '\n')

        qsys_script.close()
        subprocess.call(['sh', os.path.join(self.work_root, 'qsys.sh')])

    def _write_tcl_file(self):
        tcl_file = open(os.path.join(self.work_root, self.system.sanitized_name+'.tcl'), 'w')
        tcl_file.write("project_new " + self.system.sanitized_name + " -overwrite\n")
        tcl_file.write("set_global_assignment -name FAMILY " + self.backend.family + '\n')
        tcl_file.write("set_global_assignment -name DEVICE " + self.backend.device + '\n')
        # default to 'orpsoc_top' if top_module entry is missing
        top_module = 'orpsoc_top'
        if self.backend.top_module:
            top_module = self.backend.top_module
        tcl_file.write("set_global_assignment -name TOP_LEVEL_ENTITY " + top_module + '\n')

        for key, value in self.vlogparam.items():
            tcl_file.write("set_parameter -name {} {}\n".format(key, value))
        (src_files, incdirs) = self._get_fileset_files(['synth', 'quartus'])

        for f in src_files:
            if f.file_type in ["verilogSource",
                               "verilogSource-95",
                               "verilogSource-2001",
                               "verilogSource-2005"]:
                _type = 'VERILOG_FILE'
            elif f.file_type in ["systemVerilogSource",
                                 "systemVerilogSource-3.0",
                                 "systemVerilogSource-3.1",
                                 "systemVerilogSource-3.1a"]:
                _type = 'SYSTEMVERILOG_FILE'
            elif f.file_type in ['vhdlSource',
                                 'vhdlSource-87',
                                 'vhdlSource-93',
                                 'vhdlSource-2008']:
                _type = 'VHDL_FILE'
            elif f.file_type in ['QIP']:
                _type = 'QIP_FILE'
            elif f.file_type in ['SDC']:
                _type = 'SDC_FILE'
            elif f.file_type in ['tclSource']:
                tcl_file.write("source {}\n".format(f.name.replace('\\', '/')))
                _type = None
            elif f.file_type in ['user']:
                _type = None
            else:
                _type = None
                _s = "{} has unknown file type '{}'"
                utils.pr_warn(_s.format(f.name,
                                        f.file_type))
            if _type:
                _s = "set_global_assignment -name {} {}\n"
                tcl_file.write(_s.format(_type,
                                         f.name.replace('\\', '/')))

        for include_dir in incdirs:
            tcl_file.write("set_global_assignment -name SEARCH_PATH " + include_dir.replace('\\', '/') + '\n')

        for f in self.backend.sdc_files:
            dst_dir = os.path.join(self.src_root, self.system.sanitized_name)
            sdc_file = os.path.relpath(os.path.join(dst_dir, f.name), self.work_root)
            tcl_file.write("set_global_assignment -name SDC_FILE " + sdc_file.replace('\\', '/') + '\n')

        # NOTE: The relative path _have_ to be used here, if the absolute path
        # is used, quartus_asm will fail with an error message that
        # sdram_io.pre.h can't be read or written.
        for f in self.qip_files:
            tcl_file.write("set_global_assignment -name QIP_FILE " +
                           os.path.relpath(f, self.work_root).replace('\\', '/') + '\n')

        tcl_files = self.backend.tcl_files
        for f in tcl_files:
            tcl_file.write(open(os.path.join(self.system.files_root, f.name)).read())
        tcl_file.close()

    def _write_makefile(self):
        quartus_options = self.backend.quartus_options
        makefile = open(os.path.join(self.work_root, 'Makefile'), 'w')
        makefile.write("DESIGN_NAME = " + self.system.sanitized_name + "\n")
        makefile.write("QUARTUS_OPTIONS = " + quartus_options + "\n")
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()

    def build(self, args):
        super(Quartus, self).build(args)

        utils.Launcher('make', cwd=self.work_root).run()

        super(Quartus, self).done()

    def pgm(self, remaining):
        args = ['--mode=jtag']
        args += remaining
        args += ['-o']
        args += ['p;' + self.system.sanitized_name + '.sof']
        utils.Launcher('quartus_pgm', args, cwd=self.work_root).run()
