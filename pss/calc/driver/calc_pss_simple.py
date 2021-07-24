from qgis.core import *
import qgis.utils
import sys
import pandas as pd

from qepanet.XPSS_scripts.pss_calc import PSSCalc
from qepanet.XPSS_scripts.data_mod import PSSDataMod

# USER INPUTS 

#- Boolean switches

#Simply the results by splitting into zones?
zones = False

#Run checks on pipes
checkPipes = False

#Run checks on nodes
checkNodes = False


p_flow = 11 # flow rate for each pump [gpm]  (Assumes (1) all stations have the same pump and (2) the flowrate is constant regardless of the pressure within the system)
gpd = 300 #gallons per day per EDU

l_material = 'HDPE_DR11'  #material of pipe

l_dia_table =  pd.read_csv('C://Users//mgoldbach//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins//qepanet//XPSS_scripts//pipe_dia.csv') #table used to lookup pipe information

l_rough_table = pd.read_csv('C://Users//mgoldbach//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins//qepanet//XPSS_scripts//pipe_rough.csv', index_col=0)

v_min = 2  #minimum allowable velocity in any pipe [ft/s]
v_max = 5  #maximum allowable velocity in any pipe [ft/s]
p_max = 180 #maximum allowable pressure in the pipeline [ft of water]

A = 0.5 #EPA probability calculation coefficient (default = 0.5)
B = 20 #EPA probability calculation coefficient (default = 20)

Pipe_read_in = ['length']  # Values that are to be read from qepanet other options are [diameter, roughness, minor_loss, status, description, tag_name]]
Pipe_pd_nm = ['Length [ft]'] 

export_filepath = r'C:\Users\mgoldbach\Documents\PythonProjects\pss_submittal\\'

export_filename = 'pss_analysis.csv'

export_filename_stats = 'pss_analysis_stats.csv'

export_filename_inp = 'pss_analysis_inputs.csv'

# END USER INPUTS 
#  NOTE:  This script was created to reproduce the E-One calculation.

inputs = {'Pipe Material': l_material, 'Pump Flowrate [gpm]': p_flow, 'Design EDU Flow [gpd]': gpd, 'EPA Coeff, A': A, 'EPA Coeff, B': B}

dataMod = PSSDataMod()

dataMod.log_progress("%%%%%%%%%%%%%%%%%%%% START PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%")


dataMod.log_progress("Checking qepanet system configuration...")

if dataMod.check(checkPipes, checkNodes) == True:
    raise Exception("ERROR: System geometry in not valid.")

    
dataMod.log_progress("...Done!")

calc = PSSCalc()

dataMod.log_progress("Initializing variables for PSS calculation...")

[Pipe_props, Node_props, Pipe_nodes, res, res_elev] = dataMod.initialize_from_qepanet()

dataMod.log_progress("PSS calculation initialization completed...")

dataMod.log_progress("Creating the connection matrix...")

[C, Pipe_props, sort_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, res)

dataMod.log_progress("Connection matrix created...")

#dataMod.log_progress("Calculating the number of upstream connections for each pipe...")
#
#upstream_conn = calc.get_num_upstream_conn(C)
#
#dataMod.log_progress("...Done!")

#dataMod.log_progress("Calculating the number of EDUs located at each pipe...")
#
#Pipe_props = calc.get_num_edu(C, Pipe_props)
#
#dataMod.log_progress(str(Pipe_props))
#
#dataMod.log_progress("...Done!")
#
#dataMod.log_progress("Calculating the total number of accumulated EDUs for each pipe...")
#
#Pipe_props = calc.get_accum_edu(C, Pipe_props)
#
#dataMod.log_progress(str(Pipe_props))
#
#dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating the number of EDUs and accumulated EDUs for each pipe...")

Pipe_props = calc.populate_edus(C, Pipe_props, sort_lst)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating the statistical approximation of the number of pumps operating...")

Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")


dataMod.log_progress("Calculating the genertated pump flow for each branch...")

Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")


#dataMod.log_progress("Calculating the accumulated flowrate in each branch...")
#
#Pipe_props = calc.get_accum_flow(C, Pipe_props)
#
#dataMod.log_progress(str(Pipe_props))
#
#dataMod.log_progress("...Done!")


dataMod.log_progress("Calculating the required pipe diameter for each branch...")

Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Getting the length values from qepanet...")

Pipe_props = dataMod.get_qepanet_pipe_props(Pipe_props, ['length'], ['Length [ft]'], sort_lst)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating headloss...")

[Pipe_props, C_factor] = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_rough_table)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating accumulated friction loss...")

Pipe_props = calc.get_accum_loss(Pipe_props)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Getting elevation data from qgis...")

[Pipe_props, max_elev, elev_out] = dataMod.get_qepanet_elev_data(Pipe_props, Pipe_nodes, sort_lst, res)

dataMod.log_progress("Maximum system elevation [ft]: "+str(max_elev))
dataMod.log_progress("System discharge elevation [ft]: "+str(elev_out))

dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating the TDH for each pipe...")

Pipe_props = calc.get_TDH(Pipe_props)

dataMod.log_progress(str(Pipe_props))

dataMod.log_progress("...Done!")

dataMod.log_progress("Getting calculating statistics...")

Calc_stats = calc.get_calc_stats(Pipe_props)

dataMod.log_progress("...Done!")

#dataMod.log_progress("Updating qgis vector layers...")
#
#dataMod.update_pipes_vlay(Pipe_props, C_factor, l_material)
#
#dataMod.log_progress("...Done!")

if zones is True:

    dataMod.log_progress("Thinning out report (defining zones)...")

    Pipe_props = dataMod.filter_small_pipes(C, Pipe_props, Pipe_nodes, sort_lst, C_factor, l_material, res)

    dataMod.log_progress("...Done!")

#dataMod.log_progress("Resorting report...")
#
#Pipe_props = Pipe_props.sort_values(by='Number Accumulated EDUs', ascending=False)
#                        
#dataMod.log_progress("...Done!")

dataMod.log_progress("Exporting .csv file...")

Pipe_props.to_csv(export_filepath+export_filename)

Calc_stats.to_csv(export_filepath+export_filename_stats)

Calc_inputs = dataMod.get_inputs_dataframe(inputs)

Calc_inputs.to_csv(export_filepath+export_filename_inp)

dataMod.log_progress("...Done!")

dataMod.log_progress("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")