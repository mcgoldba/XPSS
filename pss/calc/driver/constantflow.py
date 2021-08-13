from qgis.core import *
import qgis.utils
from qgis.utils import iface
#from PyQt5.QtWidgets import QDockWidget
import sys
import pandas as pd
import time
import os

from XPSS.pss.calc.report import Report
from XPSS.pss.calc.driver.driverfactory import DriverFactory
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory

from XPSS.pss.db.units import VelocityUnits, FlowUnits, LengthUnits


from . import Driver
from XPSS.pss.calc import Calc

from XPSS.logger import Logger

from .private.systemops import nEDU, nAEDU, Q, v, p
from .private.qgisinterface import update_vlay

#consoleWidget = iface.mainWindow().findChild( QDockWidget , QDockWidget, 'PythonConsole' )
#consoleWidget.console.shellOut.clearConsole()

# USER INPUTS

start_time = time.time()

#- Boolean Switches

# debug = True       #True:  Print additional information to assist in debugging
#
# zones = False       #True:  After calculating system characteristics simplify results by
#                     #        grouping into zones
#                     #False: Display results for each pipe.
#
# run_checks = False  #If True run the checks for a correct system geometry
#
# check_pipe_conns = False  #check if 2 nodes are connected to each pipe (also requires run_checks = True)
# check_node_conns = False    #check if every nodeis  connected to a pipe (also requires run_checks = True)
#
# all_pumps_on = False  # if true calculate with all pumps operating.  If false, calculate number operating edus based on specified statistical model (default EPA)
#
# calc_pipe_dia = False  # if True pipe diameters are calculated based on user specified velocity limits.
#                         # if False the diameters specified in the attribute table are used for the calculation.
#
# pipe_dia_based_zones = False  #if True zones are determined based on changes in diameter in the forcemain, otherwise divisions are based on user input
#
# #- Solver Methods
#
# op_edu_calc = 'EPA'   # define how the number of operating pumps will be calculated if all pumps are not operating.  Options are:
#                         #       "table": get value from a table based on the numbber of accumulated EDUs.
#                         #       "EPA":  calculated based on EPA Equation with the "A" and "B" coefficients as defined below.
#
#
#                         # if False pipe diameters are read from the QGIS vector layer
#
# p_calc = 'forward-sub'  #indicate how to calculate pressure.  options are:
#                         #   "fixed-point":  fixed point iteraation (convergence is not guaranteed)
#                         #   "broyden":       secant method
#                         #   "broyden-sp":    scipy's builtin version of broyden's method (a quasi-Newton method)
#                         #   "forward-sub"   forward substitution
#
# #- System Configuration Options
#
# units_dist = 1      #Units of measure for length.
#                     #Valid Options are:
#                     #   0: Meters
#                     #   1: Feet
#
# p_flow = 11 # flow rate for each pump [gpm]  (Assumes (1) all stations have the same pump and (2) the flowrate is constant regardless of the pressure within the system)
# gpd = 250 #gallons per day per EDU
#
# l_class = 'HDPE DR11'  # Pressure rating of pipe.  Options are:
#                         #       'PVC Sch. 40'
#                         #       'HDPE DR11'
# #l_material = PipeMaterial.HDPE    #material of pipe.  Options are:
#                     #   PipeMaterial.PVC:  Standard Sch40 PVC Pipe
#                     #   PipeMaterial.HDPE:  DR11 HDPE Pipe
#
#
# v_min = 2  #minimum allowable velocity in any pipe [ft/s]
# v_max = 8  #maximum allowable velocity in any pipe [ft/s]
# #p_max = 180 #maximum allowable pressure in the pipeline [ft of water]
#
# A = 1.5 #EPA probability calculation coefficient (default = 0.5)
# B = 30 #EPA probability calculation coefficient (default = 20)
#
# lateral_conn_dia = 1.25 #diameter of the lateral connection
#
# station_depth = 5 #depth from ground discharge to water level for each station
#
# #- Filepaths
#
# script_filepath = 'C://Users//mgoldbach//AppData//Roaming//QGIS//QGIS3//profiles//default//python//plugins//XPSS//pss//'
#
# l_dia_table_file = 'pipe_data//pipe_dia.csv'
#
# l_rough_table_file = 'pipe_data//pipe_rough.csv'
#
# op_edu_table_file = 'op_edu.csv'
#
# l_dia_table =  pd.read_csv(script_filepath+l_dia_table_file) #table used to lookup pipe information
#
# l_rough_table = pd.read_csv(script_filepath+l_rough_table_file, index_col=0)
#
# op_edu_table = pd.read_csv(script_filepath+op_edu_table_file)
#
# Pipe_read_in = ['length']  # Values that are to be read from qepanet other options are [diameter, roughness, minor_loss, status, description, tag_name]]
# Pipe_pd_nm = ['Length [ft]']
#
# export_filepath = r'C:\Users\mgoldbach\Documents\PythonProjects\pss_submittal'
#
# export_filename = '\pss_analysis.csv'
#
# export_filename_pipes = '\pss_analysis_pipes.csv'
#
# export_filename_nodes = '\pss_analysis_nodes.csv'
#
# export_filename_stats = '\pss_analysis_stats.csv'
#
# export_filename_pipe_sum = '\pss_analysis_pipe_sum.csv'
#
# export_filename_inp = '\pss_analysis_inputs.csv'

# END USER INPUTS
#  NOTE:  This script was created to reproduce the E-One calculation.

logger = Logger(debug=False)

@DriverFactory.register('Constant Flow')
class ConstantFlow(Driver):
        """
        Driver function for calculation with a constant flowrate specification
        """
        def __init__(self, dockwidget):
            super().__init__(dockwidget)
            self.flowrate = dockwidget.txt_flowrate.text()
            self.nAEDU = None # number of accumulated EDUs
            self.dockwidget = dockwidget


        def run(self):
            ConstantFlowRunner(self.dockwidget).run()

#This class is necessary to allow access from other 'Driver' derived classes
class ConstantFlowRunner(Driver):
    def __init__(self, dockwidget):
        super().__init__(dockwidget)

        self.flowrate = float(dockwidget.txt_flowrate.text())
        self.flowrate *= FlowUnits[dockwidget.cbo_flow_units.currentText()]
        self.flowrate = self.flowrate.to_base_units().magnitude

        self.minV = float(dockwidget.txt_min_vel.text())
        self.minV *= VelocityUnits[dockwidget.cbo_min_vel_units.currentText()]
        self.minV = self.minV.to_base_units().magnitude
        self.maxV = float(dockwidget.txt_max_vel.text())
        self.maxV *= VelocityUnits[dockwidget.cbo_max_vel_units.currentText()]
        self.maxV = self.maxV.to_base_units().magnitude

        self.fl = None # pipe friction loss
        self.afl = None # accumulated friction loss

        self.dockwidget = dockwidget

    def run(self):
        logger.debugger("Incidence Square matrix:\n"+str(self.A))

        logger.progress("Calculating the number of EDUs for each pipe...")
        self.nEDU = nEDU(self.A)
        logger.debugger("nEDUs:\n"+str(self.nEDU))
        logger.progress("...Done!")

        logger.progress("Calculating the number of accumulated EDUs...")
        self.nAEDU = nAEDU(self.nEDU)
        logger.debugger("nAEDU:\n"+str(self.nAEDU))
        logger.progress("...Done!")

        logger.progress("Calculating the number of operating EDUs...")
        #get_num_upstream_conn(self.A)
        opedumethod = OpEduMethodFactory(
                self.dockwidget,
                self.nAEDU
                ).create(self.dockwidget.cbo_op_edu_method.currentText())
        self.nOpEDU = opedumethod.calc()
        logger.debugger("nOpEDU:\n"+str(self.nOpEDU.T))
        logger.progress("...Done!")

        logger.progress("Calculating flowrates...")
        self.Q = Q(self.nOpEDU, self.flowrate)
        logger.progress("...Done!")

        logger.progress("Calculating velocities...")
        self.v = v(self)
        logger.progress("...Done!")

        logger.progress("Calculating pressures...")
        self.p = p(self)
        logger.progress("...Done!")

        update_vlay(self)

        Report(self).create()

        #
        # #logger.progress("Calculating the number of EDUs located at each pipe...")
        # #
        # #Pipe_props = calc.get_num_edu(C, Pipe_props)
        # #
        # #logger.progress(str(Pipe_props))
        # #
        # #logger.progress("...Done!")
        # #
        # #logger.progress("Calculating the total number of accumulated EDUs for each pipe...")
        # #
        # #Pipe_props = calc.get_accum_edu(C, Pipe_props)
        # #
        # #logger.progress(str(Pipe_props))
        # #
        # #logger.progress("...Done!")
        #
        # logger.progress("Calculating the number of EDUs and accumulated EDUs for each pipe...")
        #
        # Pipe_props = calc.populate_edus(C, Pipe_props, sort_lst)
        #
        # #logger.progress("Node props: \n", Node_props)
        #
        # #logger.progress(str(Pipe_props))
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Calculating the statistical approximation of the number of pumps operating...")
        #
        # if all_pumps_on:
        #     Pipe_props = calc.set_op_edu_all_pumps(Pipe_props)
        # elif op_edu_calc == 'table':
        #     Pipe_props = calc.get_op_edu_table(Pipe_props, op_edu_table)
        # else:
        #     Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)
        #
        # #logger.progress("Node props: \n", Node_props)
        #
        # #logger.progress(str(Pipe_props))
        #
        # #logger.progress("...Done!")
        #
        #
        # logger.progress("Calculating the genertated pump flow for each branch...")
        #
        # Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)
        #
        # dataMod.log_debug("Node props: \n"+str(Node_props), debug)
        #
        # dataMod.log_debug(str(Pipe_props), debug)
        #
        # #logger.progress("...Done!")
        #
        #
        # #logger.progress("Calculating the accumulated flowrate in each branch...")
        # #
        # #Pipe_props = calc.get_accum_flow(C, Pipe_props)
        # #
        # #logger.progress(str(Pipe_props))
        # #
        # #logger.progress("...Done!")
        #
        # if calc_pipe_dia is True:
        #     logger.progress("Calculating the required pipe diameter for each branch...")
        # else:
        #     logger.progress("Reading pipe diameters from the QGIS vector layer...")
        #
        # Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_class, v_min, v_max, calc_pipe_dia)
        #
        #
        # #Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)
        #
        # dataMod.log_debug("Node props: \n"+str(Node_props), debug)
        # dataMod.log_debug(str(Pipe_props), debug)
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Getting the length values from qepanet...")
        #
        # Pipe_props = dataMod.get_qepanet_pipe_props2(Pipe_props, ['length'], ['Length [ft]'])
        #
        # #logger.progress("Converting length to XPSS units...")
        #
        # #Pipe_props = calc.convert_length(Pipe_props, units_dist)
        #
        # dataMod.log_debug("Node props: \n"+str(Node_props), debug)
        # dataMod.log_debug(str(Pipe_props), debug)
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Calculating headloss...")
        #
        # [Pipe_props, C_factor] = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_class, l_rough_table)
        #
        # dataMod.log_debug("Node props: \n"+str(Node_props), debug)
        # dataMod.log_debug(str(Pipe_props['Length [ft]']), debug)
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Calculating pressures for all nodes and pipes...")
        #
        # [Pipe_props, Node_props, max_elev, elev_out] = calc.get_accum_loss_ind2(Pipe_props, Node_props, In, sort_lst, node_srt_lst, res_elev[0], p_calc, station_depth)
        #
        # #logger.progress("Node props: \n", Node_props)
        # #logger.progress(str(Pipe_props))
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Translating node pressure values to pipe values...")
        #
        # [Pipe_props] = dataMod.get_pipe_elev_data2(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev[0])
        #
        # dataMod.log_debug("Node props: \n"+str(Node_props), debug)
        # dataMod.log_debug(str(Pipe_props), debug)
        # #[Pipe_props, max_elev, elev_out] = dataMod.get_pipe_elev_ind(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev)
        #
        #
        # #logger.progress("Maximum system elevation [ft]: "+str(max_elev))
        # #logger.progress("System discharge elevation [ft]: "+str(elev_out))
        #
        # #logger.progress("...Done!")
        #
        # logger.progress("Calculating the TDH for each pipe...")
        #
        # Pipe_props = calc.get_TDH2(Pipe_props, Node_props, sort_lst, node_srt_lst)
        #
        # dataMod.log_debug(str(Pipe_props), debug)
        # #logger.progress(str(Pipe_props))
        #
        # #logger.progress("...Done!")
        #
        # #logger.progress("Calculating node pressures...")
        #
        # #Node_props = calc.get_node_pressure(Pipe_nodes, Pipe_props, Node_props, sort_lst)
        #
        # logger.progress("Getting calculation statistics...")
        #
        # Calc_stats, Pipe_len = calc.get_calc_stats(Pipe_props, max_elev)
        #
        # dataMod.log_debug(str(Pipe_props), debug)
        # #logger.progress("...Done!")
        #
        # logger.progress("Updating qgis vector layers...")
        #
        # dataMod.update_pipes_vlay(Pipe_props, C_factor, l_material)
        # dataMod.update_junctions_vlay(Node_props)
        #
        # dataMod.log_debug(str(Pipe_props), debug)
        #
        # #logger.progress("...Done!")
        #


# dataMod = PSSDataMod()
#
# inputs = {'Pipe Material': l_class, 'Pump Flowrate [gpm]': p_flow, 'Design EDU Flow [gpd]': gpd, 'EPA Coeff, A': A, 'EPA Coeff, B': B}
#
# logger.progress("%%%%%%%%%%%%%%%%%%%% START PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%")
#
# logger.progress("Validating input parameters...")
#
# if dataMod.validate_inputs(all_pumps_on, op_edu_calc, p_calc, l_material, l_class) == False:
#     raise Exception("ERROR: System input parameters are invalid.")
#
#
# logger.progress("Checking qepanet system configuration...")
#
# if run_checks is True:
#     [has_error, num_entity_err, num_pipes, num_nodes] = dataMod.check(check_pipe_conns, check_node_conns)
# else:
#     [has_error, num_entity_err, num_pipes, num_nodes] = [False, False, 0, 0]
#
# if has_error == True:
#     raise PSSDataMod.log_error("System geometry in not valid.", stop=True)
#
#
# #logger.progress("...Done!")
#
# calc = PSSCalc()
#
# logger.progress("Initializing variables for PSS calculation...")
#
# [Pipe_props, Node_props, Pipe_nodes, res, res_elev] = dataMod.initialize_from_qepanet()
#
# #logger.progress("PSS calculation initialization completed...")
#
# logger.progress("Creating the connection matrix...")
#
# [C, C_n, In, Pipe_props, sort_lst, node_srt_lst] = dataMod.create_conn_matrix(Pipe_nodes, Pipe_props, Node_props, res, num_entity_err, num_pipes, num_nodes)
#
# #logger.progress("Node props: \n", Node_props)
#
# #logger.progress("Connection matrix created...")
#
# #logger.progress("Calculating the number of upstream connections for each pipe...")
# #
# #upstream_conn = calc.get_num_upstream_conn(C)
# #
# #logger.progress("...Done!")
#
# #logger.progress("Calculating the number of EDUs located at each pipe...")
# #
# #Pipe_props = calc.get_num_edu(C, Pipe_props)
# #
# #logger.progress(str(Pipe_props))
# #
# #logger.progress("...Done!")
# #
# #logger.progress("Calculating the total number of accumulated EDUs for each pipe...")
# #
# #Pipe_props = calc.get_accum_edu(C, Pipe_props)
# #
# #logger.progress(str(Pipe_props))
# #
# #logger.progress("...Done!")
#
# logger.progress("Calculating the number of EDUs and accumulated EDUs for each pipe...")
#
# Pipe_props = calc.populate_edus(C, Pipe_props, sort_lst)
#
# #logger.progress("Node props: \n", Node_props)
#
# #logger.progress(str(Pipe_props))
#
# #logger.progress("...Done!")
#
# logger.progress("Calculating the statistical approximation of the number of pumps operating...")
#
# if all_pumps_on:
#     Pipe_props = calc.set_op_edu_all_pumps(Pipe_props)
# elif op_edu_calc == 'table':
#     Pipe_props = calc.get_op_edu_table(Pipe_props, op_edu_table)
# else:
#     Pipe_props = calc.get_op_edu_epa(Pipe_props, A, B, p_flow)
#
# #logger.progress("Node props: \n", Node_props)
#
# #logger.progress(str(Pipe_props))
#
# #logger.progress("...Done!")
#
#
# logger.progress("Calculating the genertated pump flow for each branch...")
#
# Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
#
# dataMod.log_debug(str(Pipe_props), debug)
#
# #logger.progress("...Done!")
#
#
# #logger.progress("Calculating the accumulated flowrate in each branch...")
# #
# #Pipe_props = calc.get_accum_flow(C, Pipe_props)
# #
# #logger.progress(str(Pipe_props))
# #
# #logger.progress("...Done!")
#
# if calc_pipe_dia is True:
#     logger.progress("Calculating the required pipe diameter for each branch...")
# else:
#     logger.progress("Reading pipe diameters from the QGIS vector layer...")
#
# Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_class, v_min, v_max, calc_pipe_dia)
#
#
# #Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_material, v_min, v_max)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props), debug)
#
# #logger.progress("...Done!")
#
# logger.progress("Getting the length values from qepanet...")
#
# Pipe_props = dataMod.get_qepanet_pipe_props2(Pipe_props, ['length'], ['Length [ft]'])
#
# #logger.progress("Converting length to XPSS units...")
#
# #Pipe_props = calc.convert_length(Pipe_props, units_dist)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props), debug)
#
# #logger.progress("...Done!")
#
# logger.progress("Calculating headloss...")
#
# [Pipe_props, C_factor] = calc.calc_pipe_loss_hazwil(Pipe_props, l_dia_table, l_material, l_class, l_rough_table)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props['Length [ft]']), debug)
#
# #logger.progress("...Done!")
#
# logger.progress("Calculating pressures for all nodes and pipes...")
#
# [Pipe_props, Node_props, max_elev, elev_out] = calc.get_accum_loss_ind2(Pipe_props, Node_props, In, sort_lst, node_srt_lst, res_elev[0], p_calc, station_depth)
#
# #logger.progress("Node props: \n", Node_props)
# #logger.progress(str(Pipe_props))
#
# #logger.progress("...Done!")
#
# logger.progress("Translating node pressure values to pipe values...")
#
# [Pipe_props] = dataMod.get_pipe_elev_data2(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev[0])
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props), debug)
# #[Pipe_props, max_elev, elev_out] = dataMod.get_pipe_elev_ind(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev)
#
#
# #logger.progress("Maximum system elevation [ft]: "+str(max_elev))
# #logger.progress("System discharge elevation [ft]: "+str(elev_out))
#
# #logger.progress("...Done!")
#
# logger.progress("Calculating the TDH for each pipe...")
#
# Pipe_props = calc.get_TDH2(Pipe_props, Node_props, sort_lst, node_srt_lst)
#
# dataMod.log_debug(str(Pipe_props), debug)
# #logger.progress(str(Pipe_props))
#
# #logger.progress("...Done!")
#
# #logger.progress("Calculating node pressures...")
#
# #Node_props = calc.get_node_pressure(Pipe_nodes, Pipe_props, Node_props, sort_lst)
#
# logger.progress("Getting calculation statistics...")
#
# Calc_stats, Pipe_len = calc.get_calc_stats(Pipe_props, max_elev)
#
# dataMod.log_debug(str(Pipe_props), debug)
# #logger.progress("...Done!")
#
# logger.progress("Updating qgis vector layers...")
#
# dataMod.update_pipes_vlay(Pipe_props, C_factor, l_material)
# dataMod.update_junctions_vlay(Node_props)
#
# dataMod.log_debug(str(Pipe_props), debug)
#
# #logger.progress("...Done!")
#
# logger.progress("Exporting .csv file on a per pipe basis... ")
#
# Pipe_props.to_csv(export_filepath+export_filename_pipes)
#
# Pipe_len.to_csv(export_filepath+export_filename_pipe_sum)
#
# Node_props.to_csv(export_filepath+export_filename_nodes)
#
# if zones is True:
#
#     logger.progress("Thinning out report (defining zones)...")
#
#     Pipe_props = dataMod.filter_small_pipes(C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, res_elev, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)
#
#     #Pipe_props = dataMod.filter_small_pipes_2(C, In, Pipe_props, Node_props, Pipe_nodes, sort_lst, C_factor, l_material, res, node_srt_lst, pipe_dia_based_zones, lateral_conn_dia)
#
#
#     #logger.progress("...Done!")
#
#     #logger.progress("Resorting report...")
#     #
#     #Pipe_props = Pipe_props.sort_values(by='Number Accumulated EDUs', ascending=False)
#     #
#     #logger.progress("...Done!")
#
#     logger.progress("Exporting .csv file on a per zone basis...")
#
#     Pipe_props.to_csv(export_filepath+export_filename)
#
#     Calc_stats.to_csv(export_filepath+export_filename_stats)
#
#     Calc_inputs = dataMod.get_inputs_dataframe(inputs)
#
#     Calc_inputs.to_csv(export_filepath+export_filename_inp)
#
# if zones is False:
#
#     logger.progress("Exporting .csv file on a per pipe basis...")
#
#     Pipe_props.to_csv(export_filepath+export_filename)
#
#     Calc_stats.to_csv(export_filepath+export_filename_stats)
#
#     Calc_inputs = dataMod.get_inputs_dataframe(inputs)
#
#     Calc_inputs.to_csv(export_filepath+export_filename_inp)
#
#
# logger.progress("Applying QGIS styling...")
#
# dataMod.apply_pipe_styling()
#
# #logger.progress("...Done!")
#
end_time = time.time()

logger.progress("Total Execution Time [s]: "+"{:.1f}".format(end_time - start_time))

logger.progress("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")
