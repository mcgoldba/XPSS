from qgis.core import *
import qgis.utils
from qgis.utils import iface
#from PyQt5.QtWidgets import QDockWidget
import sys
import pandas as pd
import time
import os

from XPSS.pss.calc.solvers.solverfactory import SolverFactory
from XPSS.pipedatabase import PipeMaterial, PipeClass

from . import Solver
from .constantflow import ConstantFlowRunner

from XPSS.logger import Logger

logger = Logger()

@SolverFactory.register('Centrifugal')
class Centrifugal(Solver):
    def __init__(self, params, pipedb, data=None):
        super().__init__(params, pipedb, data)

    def run(self):
        """
        Driver function for claculation with centrifugal pumps (variable
        flowrate)
        """

        logger.progress("%%%%%%%%%%%%%%%%%%%% START PSS CALC - CENTRIFUGAL %%%%%%%%%%%%%%%%%%%%")

        # Obtain intial values for iterative solver

        #logger.progress("ConstantFlow MRO: "+str(ConstantFlow.__mro__))

        self.data = ConstantFlowRunner(self.params, self.pipedb).run()

        return self.data


#
# logger.progress("Validating input parameters...")
#
# if dataMod.validate_inputs(all_pumps_on, op_edu_calc, p_calc, l_material, l_class) == False:
#     raise Exception("ERROR: System input parameters are invalid.")
#
# logger.progress("Reading pump curve information...")
#
# #dataMod.get_pump_curve(pump_database_location, pump_model)
#
# logger.progress("...Done!")
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
# logger.progress("Calculating the number of EDUs and accumulated EDUs for each pipe...")
#
# Pipe_props = calc.populate_edus(C, Pipe_props, sort_lst)
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
# logger.progress("Calculating the genertated pump flow for each branch...")
#
# Pipe_props = calc.get_flow_gen(Pipe_props, p_flow)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
#
# dataMod.log_debug(str(Pipe_props), debug)
#
# if calc_pipe_dia is True:
#     logger.progress("Calculating the required pipe diameter for each branch...")
# else:
#     logger.progress("Reading pipe diameters from the QGIS vector layer...")
#
# Pipe_props = calc.get_pipe_dia(Pipe_props, l_dia_table, l_class, v_min, v_max, calc_pipe_dia)
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props), debug)
#
# logger.progress("Getting the length values from qepanet...")
#
# Pipe_props = dataMod.get_qepanet_pipe_props2(Pipe_props, ['length'], ['Length [ft]'])
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
# logger.progress("Translating node pressure values to pipe values...")
#
# [Pipe_props] = dataMod.get_pipe_elev_data2(Pipe_props, Node_props, sort_lst, node_srt_lst, In, res_elev[0])
#
# dataMod.log_debug("Node props: \n"+str(Node_props), debug)
# dataMod.log_debug(str(Pipe_props), debug)
#
# logger.progress("Calculating the TDH for each pipe...")
#
# Pipe_props = calc.get_TDH2(Pipe_props, Node_props, sort_lst, node_srt_lst)
#
# dataMod.log_debug(str(Pipe_props), debug)
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
# end_time = time.time()
#
# logger.progress("Total Execution Time [s]: "+"{:.1f}".format(end_time - start_time))

logger.progress("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")
