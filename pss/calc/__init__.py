from qgis.core import *
import qgis.utils
import sys
import numpy as np
import pandas as pd
import warnings

import scipy.interpolate as interp
import scipy.linalg as sla
from scipy import optimize
from scipy.optimize import curve_fit
from scipy.sparse import csr_matrix
from XPSS.pipedatabase import PipeMaterial, PipeClass

from XPSS.pss import PSS

from XPSS.pss.calc.data import Data

from XPSS.logger import Logger

logger = Logger()

class Calc(PSS):

    def __init__(self, params, pipedb, data):
        super().__init__(params, pipedb)
        if not data:
            data = Data(self, params)
        self.data = data
        # self.Q = self.data.Q # flowrates
        # self.p = self.data.p # pressures
        # self.Qc = self.data.Qc # flowrate corrections
        # self.Pc = self.data.Pc #pressure corrections
        # self.dh = self.data.dh #Static heads (elevations)
        #
        # self.Cn = self.data.Cn
        # self.Cn_n = self.data.Cn_n
        # self.B = self.data.B
        # self.pipeProp = self.data.pipeProps
        # self.pipeSortList = self.data.pipeSortList
        # self.nodeSortList = self.data.nodeSortList
        #
        # self.A = self.data.A # Strictly-upper triangular incidence matrix
        #
        # #constant values:
        # self.n = self.data.n  #number of pipes / junctions
        # self.onesVec = self.data.onesVec
        #
        # self.nOpEDU = self.data.nOpEDU
        # self.nEDU = self.data.nEDU
        #
        # self.nomDia = self.data.nomDia # nominal diameter of pipes (np.array(n,1))
        # self.matl = self.data.matl # pipe material
        # self.sch = self.data.sch # pipe schedule
        #
        # self.d = self.data.d #inner pipe diameter
        # self.C = self.data.C # Hazen-Williams coefficient
        # self.roughness = self.data.roughness # Darcy-Weisbach frictino coefficient
        # self.L = self.data.L # Pipe lengths
        #
        # self.pumps = self.data.pumps # List of pumps for end nodes

    from .linearsolver import linearsolver
    #from .get_pump_curve import get_pump_curve
    #from .get_flow_pump_curve import get_flow_pump_curve
