# from qgis.core import *
# import qgis.utils
# from qgis.utils import iface
# #from PyQt5.QtWidgets import QDockWidget
# import sys
# import pandas as pd
import time
# import os

from .params import PSSParams
from XPSS.pss.report import Report
from XPSS.pss.calc.solvers.solverfactory import SolverFactory
from .qgisinterface import update_vlay

# from XPSS.pipedatabase import PipeMaterial, PipeClass

# from .solverfactory import DriverFactory
# from . import Driver
# from .constantflow import ConstantFlowRunner

from XPSS.logger import Logger

logger = Logger(debug=True)

start_time = time.time()

class Driver:
    def __init__(self, dockwidget):
        self.data = None
        self.params = PSSParams(dockwidget)
        self.report = None
        self.pipedb = dockwidget.pipedb




    def run(self):

        logger.debugger(str(self.params))

        solver = SolverFactory(self.params, self.pipedb).create(
            self.params.solver)

        #rpt_file = os.path.splitext(self.inp_file_path)[0] + '.rpt'
        #out_binary_file = os.path.splitext(self.inp_file_path)[0] + '.out'

        self.data = solver.run()

        update_vlay(solver)

        #self.report = Report(self.data)

        #self.report.create()

        end_time = time.time()

        logger.progress("Total Execution Time [s]: "+"{:.1f}".format(end_time - start_time))

        logger.progress("%%%%%%%%%%%%%%%%%%%%% END PSS CALC - SIMPLE %%%%%%%%%%%%%%%%%%%%%")
