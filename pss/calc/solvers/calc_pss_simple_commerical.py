from qgis.core import *
import qgis.utils
import sys
import pandas as pd

from qepanet.xylem_scripts.pss_calc import PSSCalc
from qepanet.xylem_scripts.data_mod import PSSDataMod

# USER INPUTS

p_flow = 11 # flow rate for each pump [gpm]  (Assumes (1) all stations have the same pump and (2) the flowrate is constant regardless of the pressure within the system)
gpd = 300 #gallons per day per EDU

l_material = 'HDPE DR11'  #material of pipe

l_dia_table =  pd.read_csv('C://Users//mgoldbach//.qgis2//python//plugins//qepanet//xylem_scripts//pipe_dia.csv') #table used to lookup pipe information

l_rough_table = pd.read_csv('C://Users//mgoldbach//.qgis2//python//plugins//qepanet//xylem_scripts//pipe_rough.csv', index_col=0)

v_min = 2  #minimum allowable velocity in any pipe [ft/s]
v_max = 5  #maximum allowable velocity in any pipe [ft/s]
p_max = 180 #maximum allowable pressure in the pipeline [ft of water]

A = 0.5 #EPA probability calculation coefficient (default = 0.5)
B = 20 #EPA probability calculation coefficient (default = 20)

Pipe_read_in = ['length']  # Values that are to be read from qepanet other options are [diameter, roughness, minor_loss, status, description, tag_name]]
Pipe_pd_nm = ['Length [ft]']

export_filepath = r'C:\Users\mgoldbach'

export_filename = '\pss_analysis.csv'

# END USER INPUTS
#  NOTE:  This script was created to reproduce the E-One calculation.


dataMod = PSSDataMod()

print("Checking qepanet system configuration...")

if dataMod.check() == True:
    raise Exception("ERROR: System geometry in not valid.")


print("...Done!")

print("Reading in pump data...")

dataMod.get

print("...Done!")

calc = PSSCalc()

print("Initializing variables for PSS calculation...")

[Pipe_nodes, Pipe_props, res] = dataMod.initialize_from_qepanet()

print("PSS calculation initialization completed...")

print("Creating the connection matrix...")

[C, Pipe_props, sort_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, res)

print("Connection matrix created...")

print("Calculating the number of EDUs located at each pipe...")

Pipe_props = calc.populate_edus_from_qepa(C, Pipe_props, sort_lst)

print(str(Pipe_props))

print("...Done!")

print("Calculating the total number of accumulated EDUs for each pipe...")

Pipe_props = calc.get_accum_edu(C, Pipe_props)

print(str(Pipe_props))

print("...Done!")

#print("Calculating the number of EDUs and accumulated EDUs for each pipe...")
#
#Pipe_props = calc.populate_edus(C, Pipe_props)
#
#print(str(Pipe_props))
#
#print("...Done!")

print("Calculating the statistical approximation of the number of pumps operating...")

Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)

print(str(Pipe_props))

print("...Done!")


print("Calculating the genertated pump flow for each branch...")

Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)

print(str(Pipe_props))

print("...Done!")


#print("Calculating the accumulated flowrate in each branch...")
#
#Pipe_props = calc.get_accum_flow(C, Pipe_props)
#
#print(str(Pipe_props))
#
#print("...Done!")


print("Calculating the required pipe diameter for each branch...")

Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)

print(str(Pipe_props))

print("...Done!")

print("Getting the length values from qepanet...")

Pipe_props = dataMod.get_qepanet_pipe_props(Pipe_props, ['length'], ['Length [ft]'], sort_lst)

print(str(Pipe_props))

print("...Done!")

print("Calculating headloss...")

Pipe_props = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_rough_table)

print(str(Pipe_props))

print("...Done!")

print("Calculating accumulated friction loss...")

Pipe_props = calc.get_accum_loss(Pipe_props)

print(str(Pipe_props))

print("...Done!")

print("Getting elevation data from qgis...")

[Pipe_props, max_elev, elev_out] = dataMod.get_qepanet_elev_data(Pipe_props, Pipe_nodes, sort_lst, res)

print("Maximum system elevation [ft]: "+str(max_elev))
print("System discharge elevation [ft]: "+str(elev_out))

print("...Done!")

print("Calculating the TDH for each pipe...")

Pipe_props = calc.get_TDH(Pipe_props)

print(str(Pipe_props))

print("...Done!")


print("Exporting .csv file...")

Pipe_props.to_csv(export_filepath+export_filename)

print("...Done!")
