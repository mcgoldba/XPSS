import numpy as np
import math
from copy import deepcopy

from XPSS.pss.db.pipedatabase import PipeDatabase
from XPSS.pss.db.units import LengthUnits

from XPSS.pss.calc.nomdia.nomdiafactory import NomDiaFactory
from XPSS.pss.calc.flowheadrelations.flowheadrelationsfactory import \
    FlowHeadRelationsFactory

from .operations import read_pipedb

from XPSS.logger import Logger

logger = Logger(debug=False)

def nEDU(A):

    n, _ = A.shape

    ones = np.ones((n,1), dtype=int)

    logger.debugger("ones:\n"+str(ones))
    logger.debugger("ones shape: "+str(ones.shape))
    logger.debugger("ones type: "+str(type(ones)))

    nUpPipes = np.array((A-np.eye(n))@ones, dtype=int)

    logger.debugger("nUpPipes:\n"+str(nUpPipes))
    logger.debugger("nUpPipes shape: "+str(nUpPipes.shape))
    logger.debugger("nUpPipes type: "+str(type(nUpPipes)))

    #nEDUV = np.array([(one^bool(n))[0] for one,n in zip(ones,nUpPipes)])

    endNodeInv = nUpPipes.astype(bool).astype(int)

    logger.debugger("endNodeInv:\n"+str(endNodeInv))

    nEDUV = ones^endNodeInv

    logger.debugger("nEDUs:\n"+str(nEDUV))

    return nEDUV

def nAEDU(nEDU):
    #TODO: Optimize this method
    nEDU = nEDU.flatten()
    nAEDU = deepcopy(nEDU.flatten())

    nAEDU[0] = np.sum(nEDU)

    # Parse the system from the root node (Reservoir) to the branches
    nT = nAEDU[0] # number of total downstream EDUs
    nE = 0 # number of parsed end nodes
    for i in range(1,len(nAEDU)):
        if nEDU[i]:
            nE += 1
        else:
            nAEDU[i] = nT - nE
            nE = 0
            nT = nAEDU[i]

    logger.debugger("nAEDU:\n"+str(nAEDU))

    return nAEDU.reshape(-1, 1)

def Q(nOpEDU, flowrate):
    """
    Calculates the flowrate in a pipe based on the number of operating EDUs

    Parameters
    ----------

    nOpEDU : np.array_like
        THe number of operating edus

    flowrate : float
        The pump flowrate

    Returns
    -------

    Q : np.array_like
        The flowrate within each pipe

    """
    #TODO: Implement as Factory Method

    return nOpEDU*flowrate


def Area(pssvars, d=None):
    """calculate the pipe cross-sectional area from nominal pipe diameter"""

    material = self.dockwidget.txt_pip

    pipedb = pssvars.dockwidget.pipedb

    if isinstance(material, str):
        latID = pipedb.get(material, sch, latDia)
        diadb = pipedb.get(material, sch).diameters
        units = LengthUnits[pipedb.get(material, sch).baseunits]

        logger.debugger("units: "+str(units))
    else:
        logger.error("Material specification must be a string value")

    nomDia = np.empty(Q.shape)

def v(pssvars):
    """Calculates velocity"""

    return pssvars.Q/(math.pi*d(pssvars)**2/4)

def d(pssvars):
    "Inner pipe diameter."
    if not pssvars.d:

        read_pipedb(pssvars)

        logger.debugger("materials: "+str(pssvars.matl))

        pssvars.d = pssvars.dockwidget.pipedb.get(
            pssvars.matl, pssvars.sch, pssvars.nomDia)

    return pssvars.d

def p(pssvars):
    """Calculates the pressure from flowrate"""

    return afl(pssvars) + dh(pssvars)


def afl(pssvars, force = False):
    """Calculates the accumulated friction loss"""

    if pssvars.afl is None or force == True:
        pssvars.afl = np.add.accumulate(fl(pssvars))

    return pssvars.afl

# def dp(pssvars, force = False):
#     """Calculate pressure change in a pipe"""
#
#     pssvars.p = hl(pssvars) + dh(pssvars)


def fl(pssvars, force=False):
    """Calculates the friction loss in pipe"""

    if pssvars.fl is None or force == True:
        fhrelation = FlowHeadRelationsFactory(pssvars).create(
            pssvars.dockwidget.cbo_friction_loss_eq.currentText())
        pssvars.fl = fhrelation(pssvars.Q)
    return pssvars.fl

def dh(pssvars):
    """Calculates the static head for nodes give elevations."""

    if pssvars.dh is None:
        pssvars.dh = pssvars.nodeProps['Elevation [ft]'].to_numpy() - \
                     pssvars.nodeProps['Elevation [ft]'].to_numpy()[0]
    return pssvars.dh

def C(pssvars):
    """Returns the appropriate Hazen-Williams coefficient"""

    if pssvars.C is None:
        read_pipedb(pssvars)
        pssvars.C = np.array([pssvars.pipedb[mat].cfactor for mat in pssvars.material])
    return pssvars.C

def L(pssvars):
    """Get the pipe length from QGIS"""

    if pssvars.L is None:

        distance = qgis.core.QgsDistanceArea()

        layer = qgis.utils.plugins["XPSS"].params.pipes_vlay

        lyr_crs = layer.crs()

        elps = QgsProject.instance().ellipsoid()
        elps_crs = QgsCoordinateReferenceSystem()
        elps_crs.createFromUserInput(elps)
        self.log_progress("Map Ellipsoid: "+str(elps))

        #transform = iface.mapCanvas().mapSettings().transformContext()
        trans_context = QgsCoordinateTransformContext()
        trans_context.calculateDatumTransforms(lyr_crs, elps_crs)

        distance.setEllipsoid(elps)
        distance.setSourceCrs(lyr_crs, trans_context)
        units = qgis.core.QgsUnitTypes

        logger.debugger("units: "+str(units))

        #get_lst is the qepanet parameter field name for the attribute

        #sort_lst = map(str, sort_lst)  #convert the array of ints to an array of strings
        #df = self.pipe_fts.filter(get_lst, axis=1) #extract columns from qepanet data
        len_ = []
        features = layer.getFeatures()
        self.log_progress("Converting from "+units.toString(units.DistanceMeters)+" to "+units.toString(calc_units)+".")
        factor = QgsUnitTypes.fromUnitToUnitFactor(units.DistanceMeters, calc_units) ## TODO: Soft code
        self.log_progress("Conversion factor: "+str(factor))

        for feature in features:
            l_calc = distance.measureLength(feature.geometry())*factor
            len_.append(l_calc)#extract length from the QgsFeature
            self.log_progress(feature['id']+": "+str(l_calc))

        pssvars.L = len_

    return pssvars.L
