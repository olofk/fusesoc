import os.path
import shutil
from fusesoc import utils

from fusesoc.build.backend import Backend
class Ise(Backend):

    TCL_FILE_TEMPLATE = """

project new {design}
project set family {family}
project set device {device}
project set package {package}
project set speed {speed}
project set "Generate Detailed MAP Report" true
project set "Verilog Include Directories" "{verilog_include_dirs}" -process "Synthesize - XST"
{source_files}
project set top "{top_module}"
"""

    TCL_FUNCTIONS = """
process run "Generate Programming File"
"""

    PGM_FILE_TEMPLATE = """
# Batch script for programming the device using a JTAG interface.
# Used with:
# $ impact -batch {pgm_file}

setMode -bscan
setCable -port auto
addDevice -p 1 -file {bit_file}
program -p 1
saveCDF -file {cdf_file}
quit
"""

    def configure(self, args):
        super(Ise, self).configure(args)
        self._write_tcl_file()

    def _write_tcl_file(self):
        (src_files, incdirs) = self._get_fileset_files(['synth', 'ise'])
        _ucf_path = os.path.relpath(os.path.join(self.src_root, self.system.sanitized_name), self.work_root)
        ucf_files = [os.path.join(_ucf_path, f.name) for f in self.backend.ucf_files]
        tcl_file = open(os.path.join(self.work_root, self.system.sanitized_name+'.tcl'),'w')
        source_files = ""
        _libraries = []
        for f in src_files:
            if f.logical_name:
                if not f.logical_name in _libraries:
                    source_files += 'lib_vhdl new {}\n'.format(f.logical_name)
                    _libraries.append(f.logical_name)
                _s = 'xfile add {} -lib_vhdl {}\n'
                source_files += _s.format(f.name,
                                          f.logical_name)
            else:
                source_files +='xfile add {}\n'.format(f.name)
        for f in ucf_files:
            source_files += 'xfile add '+f
        tcl_file.write(self.TCL_FILE_TEMPLATE.format(
            design               = self.system.sanitized_name,
            family               = self.backend.family,
            device               = self.backend.device,
            package              = self.backend.package,
            speed                = self.backend.speed,
            top_module           = self.backend.top_module,
            verilog_include_dirs = '|'.join(incdirs),
            source_files = source_files))

        if self.vlogparam:
            s = 'project set "Generics, Parameters" "{}" -process "Synthesize - XST"\n'
            tcl_file.write(s.format('|'.join([k+'='+str(v) for k,v in self.vlogparam.items()])))
        for f in self.backend.tcl_files:
            tcl_file.write(open(os.path.join(self.system.files_root, f.name)).read())

        tcl_file.write(self.TCL_FUNCTIONS)
        tcl_file.close()

    def build(self, args):
        super(Ise, self).build(args)

        utils.Launcher('xtclsh', [os.path.join(self.work_root, self.system.sanitized_name+'.tcl')],
                           cwd = self.work_root,
                           errormsg = "Failed to make FPGA load module").run()
        super(Ise, self).done()

    def pgm(self, remaining):
        pgm_file_name = os.path.join(self.work_root, self.system.sanitized_name+'.pgm')
        self._write_pgm_file(pgm_file_name)
        utils.Launcher('impact', ['-batch', pgm_file_name],
                           cwd = self.work_root,
                           errormsg = "impact tool returned an error").run()

    def _write_pgm_file(self, pgm_file_name):
        pgm_file = open(pgm_file_name,'w')
        pgm_file.write(self.PGM_FILE_TEMPLATE.format(
            pgm_file             = pgm_file_name,
            bit_file             = os.path.join(self.work_root, self.backend.top_module+'.bit'),
            cdf_file             = os.path.join(self.work_root, self.backend.top_module+'.cdf')))
        pgm_file.close()
