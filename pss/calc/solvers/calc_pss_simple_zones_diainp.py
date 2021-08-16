# Customize this starter script by adding code
# to the run_script function. See the Help for
# complete information on how to create a script
# and use Script Runner.

""" Your Description of the script goes here """

# Some commonly used imports

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *
from qgis.gui import *
import qgis.utils

import sys
import pandas as pd



from qepanet.xylem_scripts.pss_calc import PSSCalc
from qepanet.xylem_scripts.data_mod import PSSDataMod



    

# USER INPUTS 



p_flow = 11 # flow rate for each pump [gpm]  (Assumes (1) all stations have the same pump and (2) the flowrate is constant regardless of the pressure within the system)

gpd = 300 #gallons per day per EDU



l_material = 'HDPE_DR11'  #material of pipe

script_filepath = 'C://Users//mgoldbach//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins//qepanet//xylem_scripts//'

l_dia_table_file = 'pipe_data//pipe_dia.csv'

l_rough_table_file = 'pipe_data//pipe_rough.csv'

op_edu_table_file = 'op_edu.csv'

l_dia_table =  pd.read_csv(script_filepath+l_dia_table_file) #table used to lookup pipe information

l_rough_table = pd.read_csv(script_filepath+l_rough_table_file, index_col=0)

op_edu_table = pd.read_csv(script_filepath+op_edu_table_file)

v_min = 2  #minimum allowable velocity in any pipe [ft/s]

v_max = 5  #maximum allowable velocity in any pipe [ft/s]

p_max = 180 #maximum allowable pressure in the pipeline [ft of water]



A = 0.5 #EPA probability calculation coefficient (default = 0.5)

B = 20 #EPA probability calculation coefficient (default = 20)



Pipe_read_in = ['length']  # Values that are to be read from qepanet other options are [diameter, roughness, minor_loss, status, description, tag_name]]

Pipe_pd_nm = ['Length [ft]'] 



export_filepath = r'C:\Users\mgoldbach\Documents\PythonProjects\pss_submittal'

export_filename = '\pss_analysis.csv'

export_filename_pipes = '\pss_analysis_pipes.csv'

export_filename_stats = '\pss_analysis_stats.csv'

export_filename_pipe_sum = '\pss_analysis_pipe_sum.csv'

export_filename_inp = '\pss_analysis_inputs.csv'



# END USER INPUTS 

#  NOTE:  This script was created to reproduce the E-One calculation.  



#  The script extracts pipe diameter info from QGIS rather than calculating based on num EDUs



inputs = {'Pipe Material': l_material, 'Pump Flowrate [gpm]': p_flow, 'Design EDU Flow [gpd]': gpd, 'EPA Coeff, A': A, 'EPA Coeff, B': B}



print("%%%%%%%%%%%%%%%%%%%% START PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%")





dataMod = PSSDataMod()



print("Checking qepanet system configuration...")



if dataMod.check() == True:

    raise Exception("ERROR: System geometry in not valid.")





#print("...Done!")



calc = PSSCalc()



print("Initializing variables for PSS calculation...")



[Pipe_props, Pipe_nodes, res] = dataMod.initialize_from_qepanet()



#print("PSS calculation initialization completed...")



print("Creating the connection matrix...")



[C, Pipe_props, sort_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, res)



#print("Connection matrix created...")



#print("Calculating the number of upstream connections for each pipe...")

#

#upstream_conn = calc.get_num_upstream_conn(C)

#

#print("...Done!")



#print("Calculating the number of EDUs located at each pipe...")

#

#Pipe_props = calc.get_num_edu(C, Pipe_props)

#

#print(str(Pipe_props))

#

#print("...Done!")

#

#print("Calculating the total number of accumulated EDUs for each pipe...")

#

#Pipe_props = calc.get_accum_edu(C, Pipe_props)

#

#print(str(Pipe_props))

#

#print("...Done!")



print("Calculating the number of EDUs and accumulated EDUs for each pipe...")



Pipe_props = calc.populate_edus(C, Pipe_props, sort_lst)



#print(str(Pipe_props))



#print("...Done!")



print("Calculating the statistical approximation of the number of pumps operating...")



Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)



#print(str(Pipe_props))



#print("...Done!")





print("Calculating the genertated pump flow for each branch...")



Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)



#print(str(Pipe_props))



#print("...Done!")





#print("Calculating the accumulated flowrate in each branch...")

#

#Pipe_props = calc.get_accum_flow(C, Pipe_props)

#

#print(str(Pipe_props))

#

#print("...Done!")





#print("Calculating the required pipe diameter for each branch...")

#

#Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)

#

#print(str(Pipe_props))

#

#print("...Done!")



print("Reading pipe diameter information from QGIS...")



Pipe_props = dataMod.get_qepanet_pipe_props(Pipe_props, ['diameter'], ['Diameter [in]'])



#print("...Done!")



print("Calculating the maximum velocity...")



Pipe_props = calc.calc_velocity(Pipe_props, l_dia_table, l_material)



#print("...Done!")



print("Getting the length values from qepanet...")



Pipe_props = dataMod.get_qepanet_pipe_props(Pipe_props, ['length'], ['Length [ft]'])



#print(str(Pipe_props))



#print("...Done!")



print("Calculating headloss...")



[Pipe_props, C_factor] = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_rough_table)



#print(str(Pipe_props))



#print("...Done!")



print("Calculating accumulated friction loss...")



Pipe_props = calc.get_accum_loss(Pipe_props)



#print(str(Pipe_props))



#print("...Done!")



print("Getting elevation data from qgis...")



[Pipe_props, max_elev, elev_out] = dataMod.get_qepanet_elev_data(Pipe_props, Pipe_nodes, sort_lst, res)



#print("Maximum system elevation [ft]: "+str(max_elev))

#print("System discharge elevation [ft]: "+str(elev_out))



#print("...Done!")



print("Calculating the TDH for each pipe...")



Pipe_props = calc.get_TDH(Pipe_props)



#print(str(Pipe_props))



#print("...Done!")



print("Getting calculating statistics...")



Calc_stats = calc.get_calc_stats(Pipe_props, max_elev)



#print("...Done!")



#print("Updating qgis vector layers...")

#

#dataMod.update_pipes_vlay(Pipe_props, C_factor, l_material)

#

#print("...Done!")

print("Exporting .csv file a on per pipe basis... ")

Pipe_props.to_csv(export_filepath+export_filename_pipes)

Pipe_len.to_csv(export_filepath+export_filename_pipe_sum)

print("Thinning out report (defining zones)...")



Pipe_props = dataMod.filter_small_pipes(C, Pipe_props, Pipe_nodes, sort_lst, C_factor, l_material, res)



#print("...Done!")



#print("Resorting report...")

#

#Pipe_props = Pipe_props.sort_values(by='Number Accumulated EDUs', ascending=False)

#                        

#print("...Done!")



print("Exporting .csv file on a per zone basis...")

Pipe_props.to_csv(export_filepath+export_filename)

Calc_stats.to_csv(export_filepath+export_filename_stats)

Calc_inputs = dataMod.get_inputs_dataframe(inputs)

Calc_inputs.to_csv(export_filepath+export_filename_inp)



#print("...Done!")



print("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")