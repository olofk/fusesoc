class Simulator:
#    def __init__(self, simulator):
#        #FIXME: Return a simulator subclass here?
#        pass
    def run(system, config, simulator):
        rtl_files = system.get_rtl_files() + system.get_tb_files()
        
#    def rtl_files(self):
        
