import os
import platform
from .simulator import Simulator
import logging
from fusesoc.utils import Launcher
import time
from shutil import copyfile

logger = logging.getLogger(__name__)

class Xsim(Simulator):

    def configure(self, args):
        super(Xsim, self).configure(args)
        self._generate_xci_sim_scripts()
        self._write_config_files()

    def _write_config_files(self):
        xsim_file = 'xsim.prj'
        f1 = open(os.path.join(self.work_root,xsim_file),'w')
        self.incdirs = set()
        src_files = []

        (src_files, self.incdirs) = self._get_fileset_files(force_slash=True)
        for src_file in src_files:
            if src_file.file_type in ["verilogSource",
		                      "verilogSource-95",
		                      "verilogSource-2001"]:
                f1.write('verilog work ' + src_file.name + '\n')
            elif src_file.file_type in ["vhdlSource",
                                        "vhdlSource-87",
                                        "vhdlSource-93"]:
                f1.write('vhdl work ' + src_file.logical_name + " " + src_file.name + '\n')
            elif src_file.file_type in ['vhdlSource-2008']:
                f1.write('vhdl2008 ' + src_file.logical_name + " " + src_file.name + '\n')
            elif src_file.file_type in ["systemVerilogSource",
                                        "systemVerilogSource-3.0",
                                        "systemVerilogSource-3.1",
                                        "systemVerilogSource-3.1a",
                                        "verilogSource-2005"]:
                f1.write('sv work ' + src_file.name + '\n')
            elif src_file.file_type in ["xci"]:
                pass
            elif src_file.file_type in ["datSource"]:
                pass
            else:
                _s = "{} has unknown file type '{}'"
                logger.warning(_s.format(src_file.name, src_file.file_type))
        f1.close()

        tcl_file = 'xsim.tcl'
        f2 = open(os.path.join(self.work_root,tcl_file),'w')
        f2.write('add_wave -radix hex /\n')
        f2.write('run all\n')
        f2.close()

    def _generate_xci_sim_scripts(self):
        # make project from all xci
        (src_files, self.incdirs) = self._get_fileset_files(force_slash=True)
        xci_ip = []
        for src_file in src_files:
            if src_file.file_type == 'xci':
                xci_ip.append(src_file.name);

        if len(xci_ip)>0:
            tcl_file = open(os.path.join(self.work_root, 'xci_sim.tcl'), 'w')
            ipconfig = 'create_project ' + self.name + '_xci_sim\n'
            ipconfig += 'set_property \"simulator_language\" \"Mixed\" [current_project]\n'
            ipconfig += '\n'.join(['read_ip '+s for s in xci_ip])+'\n'
            ipconfig += 'upgrade_ip [get_ips]\n'
            #  ipconfig += '\n'.join(['generate_target simulation [get_files '+os.path.basename(s)+']'\
            ipconfig += '\n'.join(['generate_target all [get_files '+ s +']' for s in xci_ip]) + '\n'
            ipconfig += '\n'.join(['export_ip_user_files -of_objects [get_files '+ s +'] -no_script -ip_user_files_dir '+ self.work_root + ' -force -quiet' for s in xci_ip]) + '\n'
            ipconfig += '\n'.join(['create_ip_run [get_files ' + s + ']' for s in xci_ip]) + '\n'
            ipconfig += '\n'.join(['launch_runs ' +os.path.splitext(os.path.basename(s))[0]+'_synth_1' for s in xci_ip]) + '\n'
            ipconfig += '\n'.join(['wait_on_run '+os.path.splitext(os.path.basename(s))[0]+'_synth_1' for s in xci_ip]) + '\n'
            ipconfig += '\n'.join(['export_simulation -directory . -simulator xsim -of_objects [get_files '+ s +'] -ip_user_files_dir . -force -quiet' for s in xci_ip])
            tcl_file.write(ipconfig)

        tcl_file = 'xsim.tcl'
        f2 = open(os.path.join(self.work_root,tcl_file),'w')
        f2.write('add_wave -radix hex /\n')
        f2.write('run all\n')
        f2.close()

        tcl_file_name = os.path.join(self.work_root, 'xci_sim.tcl')
        if (os.path.isfile(tcl_file_name)):
            Launcher('vivado', ['-mode', 'batch', '-source', tcl_file_name],
                               shell=platform.system() == 'Windows',
                               cwd = self.work_root,
                               errormsg = "Failed to generate simulation scripts from xci").run()


    def build_main(self):

        #  tcl_file_name = os.path.join(self.work_root, 'xci_sim.tcl')
        #  if (os.path.isfile(tcl_file_name)):
        #      Launcher('vivado', ['-mode', 'batch', '-source', tcl_file_name],
        #                         cwd = self.work_root,
        #                         errormsg = "Failed to generate simulation scripts from xci").run()

        (src_files, self.incdirs) = self._get_fileset_files()
        for src_file in src_files:
            if src_file.file_type == 'xci':
                ip_name = os.path.splitext(os.path.basename(src_file.name))[0]
                vlog_prj  = os.path.join(self.work_root, ip_name , 'xsim', 'vlog.prj')
                vhdl_prj  = os.path.join(self.work_root, ip_name , 'xsim', 'vhdl.prj')
                glbl_file = os.path.join(self.work_root, ip_name , 'xsim', 'glbl.v')

                if os.path.isfile(vlog_prj):
                    Launcher('xvlog', ['--prj', vlog_prj],
                             shell=platform.system() == 'Windows',
                             cwd      = self.work_root,
                             errormsg = "Failed to compile Xsim simulation model").run()

                if os.path.isfile(vhdl_prj):
                    Launcher('xvhdl', ['--prj', vhdl_prj],
                             shell=platform.system() == 'Windows',
                             cwd      = self.work_root,
                             errormsg = "Failed to compile Xsim simulation model").run()

                if os.path.isfile(vlog_prj):
                    Launcher('xvlog', [glbl_file],
                             shell=platform.system() == 'Windows',
                             cwd      = self.work_root,
                             errormsg = "Failed to compile Xsim simulation model").run()

        #  .dat should be src_file for sim
        for src_file in src_files:
            #  print(src_file.name + ' type: ' + src_file.file_type)
            if src_file.file_type in ["datSource"]:
                #  print('Copying file...')
                #  print(src_file.name)
                # print(os.path.join(self.work_root, os.path.basename(src_file.name)))
                copyfile(os.path.join(self.work_root,src_file.name), os.path.join(self.work_root, os.path.basename(src_file.name)))

        #Check if any VPI modules are present and display warning
        if len(self.vpi_modules) > 0:
            modules = [m['name'] for m in self.vpi_modules]
            logger.error('VPI modules not supported by Xsim: %s' % ', '.join(modules))

        #Build simulation model
        args = []
        args += [ self.toplevel]
        args += [ 'glbl' ]
        args += ['--prj', 'xsim.prj']      # list of design files
        args += ['--timescale', '1ps/1ps'] # default timescale to prevent error if unspecified
        args += ['--snapshot', 'fusesoc']  # name of the design to simulate
        args += ['--debug', 'typical']     # capture waveforms
        args += ['--relax']     # capture waveforms

        #Get IP libraries
        libs=[]
        for src_file in src_files:
            if src_file.file_type == 'xci':
                ip_name = os.path.splitext(os.path.basename(src_file.name))[0]
                ini_file = os.path.join(self.work_root, ip_name ,'xsim' , 'xsim.ini')
                with open(ini_file, 'r') as f:
                    for line in f:
                        lib_name = line.split('=')[0]
                        if lib_name not in libs:
                            args += ['-L', lib_name]
                            libs.append(lib_name)

        args += ['-L', 'work']
        args += ['-L', 'unisims_ver']
        args += ['-L', 'unimacro_ver']
        args += ['-L', 'secureip']

        for include_dir in self.incdirs:
            args += ['-i', include_dir]

        for key, value in self.vlogparam.items():
            args += ['--generic_top', '{}={}'.format(key, self._param_value_str(value))]

        #  if 'xsim_options' in self.tool_options:
        #      args += self.tool_options['xsim_options']

        Launcher('xelab', args,
                 shell=platform.system() == 'Windows',
                 cwd      = self.work_root,
                 errormsg = "Failed to compile Xsim simulation model").run()

    def run(self, args):
        super(Xsim, self).run(args)

        #FIXME: Handle failures. Save stdout/stderr.
        args = []
        args += ['--gui']                                 # Interactive
        args += ['--tclbatch', 'xsim.tcl']                 # Simulation commands
        args += ['--log', 'xsim.log']                      # Log file
        args += ['--wdb', 'xsim.wdb']                      # Simulation waveforms database
        args += ['fusesoc']                                # Snapshot name
        # Plusargs
        for key, value in self.plusarg.items():
            args += ['--testplusarg', '{}={}'.format(key, value)]
        #FIXME Top-level parameters


        Launcher('xsim', args,
                 shell=platform.system() == 'Windows',
                 cwd = self.work_root,
                 errormsg = "Failed to run Xsim simulation").run()

        super(Xsim, self).done(args)

