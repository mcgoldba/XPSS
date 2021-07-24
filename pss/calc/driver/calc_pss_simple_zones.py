from qgis.core import *
import qgis.utils
from qgis.utils import iface
#from PyQt5.QtWidgets import QDockWidget
import sys
import pandas as pd
import time

from qepanet.XPSS_scripts.pss_calc import PSSCalc
from qepanet.XPSS_scripts.data_mod import PSSDataMod

#consoleWidget = iface.mainWindow().findChild( QDockWidget , QDockWidget, 'PythonConsole' )
#consoleWidget.console.shellOut.clearConsole()

# USER INPUTS 

start_time = time.time()

#- Boolean Switches

debug = True        #True:  Print additional information to assist in debugging

zones = False       #True:  After calculating system characteristics simply results by 
                    #        grouping into zones
                    #False: Display results for each pipe.

run_checks = True  #If True run the checks for a correct system geometry

check_pipe_conns = False  #check if 2 nodes are connected to each pipe (also requires run_checks = True) 
check_node_conns = False    #check if every nodeis  connected to a pipe (also requires run_checks = True)

all_pumps_on = False  # if true calculate with all pumps operating.  If false, calculate number operating edus based on specified statistical model (default EPA)

calc_pipe_dia = True   # if True pipe diameters are calculated based on user specified velocity limits.

pipe_dia_based_zones = False  #if True zones are determined based on changes in diameter in the forcemain, otherwise divisions are based on user input                

#- Solver Methods

op_edu_calc = 'table'  # define how the number of operating pumps will be calculated is all pumps are not operating.


                        # if False pipe diameters are read from the QGIS vector layer

p_calc = 'forward-sub'  #indicate how to calculate pressure.  options are:
                        #   "fixed-point":  fixed point iteraation (convergence is not guaranteed)
                        #   "broyden":       secant method
                        #   "broyden-sp":    scipy's builtin version of broyden's method (a quasi-Newton method)
                        #   "forward-sub"   forward sunstitution

#- System Configuration Options
                
units_dist = 1      #Units of measure for length.  
                    #Valid Options are:
                    #   0: Meters
                    #   1: Feet 
    
p_flow = 11 # flow rate for each pump [gpm]  (Assumes (1) all stations have the same pump and (2) the flowrate is constant regardless of the pressure within the system)
gpd = 250 #gallons per day per EDU
        
l_material = 'PVC'  #material of pipe

v_min = 2  #minimum allowable velocity in any pipe [ft/s]
v_max = 5  #maximum allowable velocity in any pipe [ft/s]
#p_max = 180 #maximum allowable pressure in the pipeline [ft of water]

A = 0.5 #EPA probability calculation coefficient (default = 0.5)
B = 20 #EPA probability calculation coefficient (default = 20)

lateral_conn_dia = 1.25 #diameter of the lateral connection

#- Filepaths

script_filepath = 'C://Users//mgoldbach//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins//qepanet//XPSS_scripts//'

l_dia_table_file = 'pipe_data//pipe_dia.csv'

l_rough_table_file = 'pipe_data//pipe_rough.csv'

op_edu_table_file = 'op_edu.csv'

l_dia_table =  pd.read_csv(script_filepath+l_dia_table_file) #table used to lookup pipe information

l_rough_table = pd.read_csv(script_filepath+l_rough_table_file, index_col=0)

op_edu_table = pd.read_csv(script_filepath+op_edu_table_file)

Pipe_read_in = ['length']  # Values that are to be read from qepanet other options are [diameter, roughness, minor_loss, status, description, tag_name]]
Pipe_pd_nm = ['Length [ft]'] 

export_filepath = r'C:\Users\mgoldbach\Documents\PythonProjects\pss_submittal'

export_filename = '\pss_analysis.csv'

export_filename_pipes = '\pss_analysis_pipes.csv'

export_filename_nodes = '\pss_analysis_nodes.csv'

export_filename_stats = '\pss_analysis_stats.csv'

export_filename_pipe_sum = '\pss_analysis_pipe_sum.csv'

export_filename_inp = '\pss_analysis_inputs.csv'

# END USER INPUTS 
#  NOTE:  This script was created to reproduce the E-One calculation.

inputs = {'Pipe Material': l_material, 'Pump Flowrate [gpm]': p_flow, 'Design EDU Flow [gpd]': gpd, 'EPA Coeff, A': A, 'EPA Coeff, B': B}

dataMod = PSSDataMod()

dataMod.log_progress("%%%%%%%%%%%%%%%%%%%% START PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%")




dataMod.log_progress("Validating input parameters...")

if dataMod.validate_inputs(all_pumps_on, op_edu_calc, p_calc, l_material) == False:
    raise Exception("ERROR: System input parameters are invalid.")


dataMod.log_progress("Checking qepanet system configuration...")

if run_checks is True:
    [has_error, num_entity_err, num_pipes, num_nodes] = dataMod.check(check_pipe_conns, check_node_conns)
else:
    [has_error, num_entity_err, num_pipes, num_nodes] = [False, False, 0, 0]

if has_error == True:
    raise PSSDataMod.log_error("System geometry in not valid.", stop=True)

    
#dataMod.log_progress("...Done!")

calc = PSSCalc()

dataMod.log_progress("Initializing variables for PSS calculation...")

[Pipe_props, Node_props, Pipe_nodes, res, res_elev] = dataMod.initialize_from_qepanet()

#dataMod.log_progress("PSS calculation initialization completed...")

dataMod.log_progress("Creating the connection matrix...")

[C, C_n, In, Pipe_props, sort_lst, node_srt_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, Node_props, res, num_entity_err, num_pipes, num_nodes)

#dataMod.log_progress("Node props: \n", Node_props)

#dataMod.log_progress("Connection matrix created...")

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

#dataMod.log_progress("Node props: \n", Node_props)

#dataMod.log_progress(str(Pipe_props))

#dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating the statistical approximation of the number of pumps operating...")

if all_pumps_on:
    Pipe_props = calc.set_op_edu_all_pumps(Pipe_props)
elif op_edu_calc == 'table':
    Pipe_props = calc.get_op_edu_table(Pipe_props, op_edu_table)
else:
    Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)

#dataMod.log_progress("Node props: \n", Node_props)

#dataMod.log_progress(str(Pipe_props))

#dataMod.log_progress("...Done!")


dataMod.log_progress("Calculating the genertated pump flow for each branch...")

Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)

dataMod.log_debug("Node props: \n"+str(Node_props), debug)

dataMod.log_debug(str(Pipe_props), debug)

#dataMod.log_progress("...Done!")


#dataMod.log_progress("Calculating the accumulated flowrate in each branch...")
#
#Pipe_props = calc.get_accum_flow(C, Pipe_props)
#
#dataMod.log_progress(str(Pipe_props))
#
#dataMod.log_progress("...Done!")

if calc_pipe_dia is True:
    dataMod.log_progress("Calculating the required pipe diameter for each branch...")
else:
    dataMod.log_progress("Reading pipe diameters from the QGIS vector layer...")

Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max, calc_pipe_dia)


#Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)

dataMod.log_debug("Node props: \n"+str(Node_props), debug)
dataMod.log_debug(str(Pipe_props), debug)

#dataMod.log_progress("...Done!")

dataMod.log_progress("Getting the length values from qepanet...")

Pipe_props = dataMod.get_qepanet_pipe_props(Pipe_props, ['length'], ['Length [ft]'])

dataMod.log_progress("Converting length to XPSS units...")

Pipe_props = calc.convert_length(Pipe_props, units_dist)

#dataMod.log_debug("Node props: \n", Node_props, debug)
#dataMod.log_debug(str(Pipe_props), debug)

#dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating headloss...")

[Pipe_props, C_factor] = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_rough_table)

dataMod.log_debug("Node props: \n"+str(Node_props), debug)
dataMod.log_debug(str(Pipe_props), debug)

#dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating pressures for all nodes and pipes...")

[Pipe_props, Node_props, max_elev, elev_out] = calc.get_accum_loss_ind(Pipe_props, Node_props, In, sort_lst, node_srt_lst, res_elev[0], p_calc)

#dataMod.log_progress("Node props: \n", Node_props)
#dataMod.log_progress(str(Pipe_props))

#dataMod.log_progress("...Done!")

dataMod.log_progress("Translating node pressure values to pipe values...")

[Pipe_props] = dataMod.get_pipe_elev_data(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev[0])

dataMod.log_debug("Node props: \n"+str(Node_props), debug)
#[Pipe_props, max_elev, elev_out] = dataMod.get_pipe_elev_ind(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev)


#dataMod.log_progress("Maximum system elevation [ft]: "+str(max_elev))
#dataMod.log_progress("System discharge elevation [ft]: "+str(elev_out))

#dataMod.log_progress("...Done!")

dataMod.log_progress("Calculating the TDH for each pipe...")

Pipe_props = calc.get_TDH(Pipe_props)

#dataMod.log_progress(str(Pipe_props))

#dataMod.log_progress("...Done!")

#dataMod.log_progress("Calculating node pressures...")

#Node_props = calc.get_node_pressure(Pipe_nodes, Pipe_props, Node_props, sort_lst)

dataMod.log_progress("Getting calculation statistics...")

Calc_stats, Pipe_len = calc.get_calc_stats(Pipe_props, max_elev)

#dataMod.log_progress("...Done!")

dataMod.log_progress("Updating qgis vector layers...")

dataMod.update_pipes_vlay(Pipe_props, C_factor, l_material)
dataMod.update_junctions_vlay(Node_props)


#dataMod.log_progress("...Done!")

dataMod.log_progress("Exporting .csv file on a per pipe basis... ")

Pipe_props.to_csv(export_filepath+export_filename_pipes)

Pipe_len.to_csv(export_filepath+export_filename_pipe_sum)

Node_props.to_csv(export_filepath+export_filename_nodes)

if zones is True:

    dataMod.log_progress("Thinning out report (defining zones)...")

    Pipe_props = dataMod.filter_small_pipes(C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, res_elev, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)

    #Pipe_props = dataMod.filter_small_pipes_2(C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)


    #dataMod.log_progress("...Done!")

    #dataMod.log_progress("Resorting report...")
    #
    #Pipe_props = Pipe_props.sort_values(by='Number Accumulated EDUs', ascending=False)
    #                        
    #dataMod.log_progress("...Done!")

    dataMod.log_progress("Exporting .csv file on a per zone basis...")

    Pipe_props.to_csv(export_filepath+export_filename)

    Calc_stats.to_csv(export_filepath+export_filename_stats)

    Calc_inputs = dataMod.get_inputs_dataframe(inputs)

    Calc_inputs.to_csv(export_filepath+export_filename_inp)

if zones is False:
    
    dataMod.log_progress("Exporting .csv file on a per pipe basis...")

    Pipe_props.to_csv(export_filepath+export_filename)

    Calc_stats.to_csv(export_filepath+export_filename_stats)

    Calc_inputs = dataMod.get_inputs_dataframe(inputs)

    Calc_inputs.to_csv(export_filepath+export_filename_inp)
    
    
dataMod.log_progress("Applying QGIS styling...")

dataMod.apply_pipe_styling()

#dataMod.log_progress("...Done!")

end_time = time.time()

dataMod.log_progress("Total Execution Time [s]: "+"{:.1f}".format(end_time - start_time))

dataMod.log_progress("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")