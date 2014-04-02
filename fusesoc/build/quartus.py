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

    TOOL_NAME = 'quartus'
    def __init__(self, system):
        super(Quartus, self).__init__(system)
        self.work_root = os.path.join(self.build_root, 'bld-'+self.TOOL_NAME)

    def configure(self):
        super(Quartus, self).configure()
        self._run_qsys()
        self._write_tcl_file()
        self._write_makefile()

    # Runs qsys if a 'qsys_files' entry can be found under the quartus section
    def _run_qsys(self):
        self.qip_files = []
        if not 'qsys_files' in self.system.backend:
            return

        qsys_script = open(os.path.join(self.work_root, 'qsys.sh'),'w')

        for f in self.system.backend['qsys_files'].split():
            src_file = os.path.join(self.systems_root, self.system.name, f)
            dst_file = os.path.join(self.work_root, f)
            dst_dir = os.path.dirname(dst_file)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            shutil.copyfile(src_file, dst_file)

            args = []
            args += ['--project-directory=' + dst_dir]
            args += ['--output-directory=' +
                     os.path.join(self.build_root, 'src/qsys')]
            args += ['--report-file=bsf:' +
                     os.path.join(dst_dir, self.system.name+'.bsf')]
            args += ['--system-info=DEVICE_FAMILY=' +
                     self.system.backend['family']]
            args += ['--system-info=DEVICE=' +
                     self.system.backend['device']]
            args += ['--component-file=' + dst_file]

            qsys_script.write('ip-generate ' + ' '.join(args) + '\n');

            self.qip_files += [os.path.join(self.build_root,
                                            'src/qsys/synthesis',
                                            self.system.name+'.qip')]
            args = []
            args += ['--project-directory=' + dst_dir]
            args += ['--output-directory=' +
                     os.path.join(self.build_root, 'src/qsys/synthesis')]
            args += ['--file-set=QUARTUS_SYNTH']
            args += ['--report-file=sopcinfo:' +
                     os.path.join(dst_dir, self.system.name+'.sopcinfo')]
            args += ['--report-file=html:' +
                     os.path.join(dst_dir, self.system.name+'.html')]
            args += ['--report-file=qip:' + self.qip_files[-1]]
            args += ['--report-file=cmp:' +
                     os.path.join(dst_dir, self.system.name+'.cmp')]
            args += ['--report-file=svd']
            args += ['--system-info=DEVICE_FAMILY=' +
                     self.system.backend['family']]
            args += ['--system-info=DEVICE=' +
                     self.system.backend['device']]
            args += ['--component-file=' + dst_file]
            args += ['--language=VERILOG']

            qsys_script.write('ip-generate ' + ' '.join(args) + '\n');

        qsys_script.close()
        subprocess.call(['sh', os.path.join(self.work_root, 'qsys.sh')]);

    def _write_tcl_file(self):
        tcl_file = open(os.path.join(self.work_root, self.system.name+'.tcl'),'w')
        tcl_file.write("project_new " + self.system.name + " -overwrite\n")
        tcl_file.write("set_global_assignment -name FAMILY " + self.system.backend['family'] + '\n')
        tcl_file.write("set_global_assignment -name DEVICE " + self.system.backend['device'] + '\n')
        # default to 'orpsoc_top' if top_module entry is missing
        top_module = 'orpsoc_top'
        if 'top_module' in self.system.backend:
            top_module = self.system.backend['top_module']
        tcl_file.write("set_global_assignment -name TOP_LEVEL_ENTITY " + top_module + '\n')
        for src_file in self.src_files:
            tcl_file.write("set_global_assignment -name VERILOG_FILE " + src_file + '\n')
        for vhdl_src_files in self.vhdl_src_files:
            tcl_file.write("set_global_assignment -name VHDL_FILE " + vhdl_src_files + '\n')
        for include_dir in self.include_dirs:
            tcl_file.write("set_global_assignment -name SEARCH_PATH " + include_dir + '\n')

        #FIXME: Handle multiple SDC files. Also handle SDC files directly from cores?
        sdc_files = self.system.backend['sdc_files'].split()
        for f in sdc_files:
            src_file = os.path.join(self.systems_root, self.system.name, f)
            dst_file =os.path.join(self.work_root, f)
            if not os.path.exists(os.path.dirname(dst_file)):
                os.makedirs(os.path.dirname(dst_file))
            shutil.copyfile(src_file, dst_file)
            tcl_file.write("set_global_assignment -name SDC_FILE " + dst_file + '\n')

        # NOTE: The relative path _have_ to be used here, if the absolute path
        # is used, quartus_asm will fail with an error message that
        # sdram_io.pre.h can't be read or written.
        for f in self.qip_files:
            tcl_file.write("set_global_assignment -name QIP_FILE " +
                           os.path.relpath(f, self.work_root) + '\n')

        tcl_files = self.system.backend['tcl_files'].split()
        for f in tcl_files:
            tcl_file.write(open(os.path.join(self.systems_root, self.system.name, f)).read())
        tcl_file.close()

    def _write_makefile(self):
        quartus_options = self.system.backend.get('quartus_options', '')
        makefile = open(os.path.join(self.work_root, 'Makefile'),'w')
        makefile.write("DESIGN_NAME = " + self.system.name + "\n")
        makefile.write("QUARTUS_OPTIONS = " + quartus_options + "\n")
        makefile.write(self.MAKEFILE_TEMPLATE)
        makefile.close()

    def build(self, args):
        super(Quartus, self).build(args)

        utils.Launcher('make', cwd = self.work_root).run()

        super(Quartus, self).done()

    def pgm(self, remaining):
        args = ['--mode=jtag']
        args += remaining
        args += ['-o']
        args += ['p;' + self.system.name + '.sof']
        utils.Launcher('quartus_pgm', args, cwd=self.work_root).run()
