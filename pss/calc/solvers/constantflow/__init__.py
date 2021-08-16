from qgis.core import *
import qgis.utils
from qgis.utils import iface
#from PyQt5.QtWidgets import QDockWidget
import sys
import pandas as pd
import time
import os

from XPSS.pss.calc.solvers.solverfactory import SolverFactory
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory

from XPSS.pss.db.units import VelocityUnits, FlowUnits, LengthUnits


from .. import Solver
from XPSS.pss.calc import Calc

from XPSS.logger import Logger

from XPSS.pss.calc.systemops import nEDU, nAEDU, v, p, L
from .private import _Q
#from ..private.qgisinterface import update_vlay

logger = Logger(debug=True)

@SolverFactory.register('Constant Flow')
class ConstantFlow(Solver):
        """
        Driver function for calculation with a constant flowrate specification
        """
        def __init__(self, params, pipedb, data):
            super().__init__(params, pipedb, data)
            self.flowrate = params.flowrate


        def run(self):
            ConstantFlowRunner(self.params, self.pipedb, self.data).run()

            #update_vlay(self)

#This class is necessary to allow access from other 'Driver' derived classes
class ConstantFlowRunner(Solver):
    def __init__(self, params, pipedb, data):
        super().__init__(params, pipedb, data)

        #self.dockwidget = dockwidget

    def run(self):
        logger.debugger("Incidence Square matrix:\n"+str(self.data.A))

        logger.progress("Calculating the number of EDUs for each pipe...")
        self.data.nEDU = nEDU(self.data.A)
        logger.debugger("nEDUs:\n"+str(self.data.nEDU))
        logger.progress("...Done!")

        logger.progress("Calculating the number of accumulated EDUs...")
        self.data.nAEDU = nAEDU(self.data.nEDU)
        logger.debugger("nAEDU:\n"+str(self.data.nAEDU))
        logger.progress("...Done!")

        logger.progress("Calculating the number of operating EDUs...")
        #get_num_upstream_conn(self.A)
        opedumethod = OpEduMethodFactory(
                self.params,
                self.data.nAEDU
                ).create(self.params.opEduCalcMethod)
        self.data.nOpEDU = opedumethod.calc()
        logger.debugger("nOpEDU:\n"+str(self.data.nOpEDU.T))
        logger.progress("...Done!")

        logger.progress("Calculating flowrates...")
        self.data.Q = _Q(self.data.nOpEDU, self.params.flowrate)
        logger.progress("...Done!")

        logger.debugger("Q:\n"+str(self.data.Q))
        logger.debugger("data: "+str(self.data))

        logger.progress("Calculating velocities...")
        self.data.v = v(self.data, self.params, self.pipedb)
        logger.progress("...Done!")

        self.data.L = L(self.data)

        logger.progress("Calculating pressures...")
        self.data.p = p(self.data, self.params, self.pipedb)
        logger.progress("...Done!")

        return self.data
