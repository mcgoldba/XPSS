import pandas as pd

class UserSettings:
    
    materials
    
    def __init__(self):
        
        #- Solver Switches
        self.debug = True
        self.zones = False
        self.run_checks = True
        self.check_pipe_conns = False
        self.check_node_conns = False
        self.all_pumps_on = False
        self.calc_pipe_dia = True
        self.pipe_dia_based_zones = False
        self.op_edu_calc = 'table'
        self.p_calc = 'forward_sub'
        
        #- System Configuration Options

        self.units_dist = 1
        self.p_flow = 11
        self.gpd = 250
        self.l_material = None
        self.v_min = 2
        self.v_max = 5
        self.A = 0.5
        self.B = 20
        
        #- Filepaths
        
        self.script_filepath = r'C:/Users/mgoldbach/AppData/Roaming/QGIS/QGIS3/profiles/default/python/plugins/qepanet/XPSS_scripts/'
        self.l_dia_table_file = r'pipe_data/pipe_data.csv'
        self.l_rough_table_file = 'pipe_data/pipe_rough.csv'
        self.op_edu_table_file = 'op_edu.csv'
        self.l_dia_table = pd.read_csv(self.script_filepath+self.l_dia_table_file)
        self.l_rough_table = pd.read_csv(self.script_filepath+self.l_rough_table_file)
        
        