import numpy as np
import math
from copy import deepcopy

#from PyQt5.QtCore import *
#from PyQt5.QtGui import *
from qgis.core import QgsProject, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransformContext, QgsUnitTypes

import qgis.utils

from XPSS.pss.db.pipedatabase import PipeDatabase
from XPSS.pss.db.units import LengthUnits

from XPSS.pss.calc.nomdia.nomdiafactory import NomDiaFactory
from XPSS.pss.calc.flowheadrelations.flowheadrelationsfactory import \
    FlowHeadRelationsFactory

from XPSS.pss.calc.operations import read_pipedb

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

def Area(data, d=None):
    """calculate the pipe cross-sectional area from nominal pipe diameter"""

    material = self.dockwidget.txt_pip

    pipedb = data.dockwidget.pipedb

    if isinstance(material, str):
        latID = pipedb.get(material, sch, latDia)
        diadb = pipedb.get(material, sch).diameters
        units = LengthUnits[pipedb.get(material, sch).baseunits]

        logger.debugger("units: "+str(units))
    else:
        logger.error("Material specification must be a string value")

    nomDia = np.empty(Q.shape)

def v(data, params, pipedb):
    """Calculates velocity"""

    d(data, params, pipedb)

    logger.debugger("flow: "+str(data.Q))
    logger.debugger("diameter: "+str(data.d))

    return (data.Q/(math.pi*d(data, params, pipedb)**2/4)).to_base_units()

def d(data, params, pipedb):
    "Inner pipe diameter."
    if data.d is None:

        data = read_pipedb(data, params, pipedb)

        logger.debugger("materials: "+str(data.matl))

        data.d = pipedb.get(
            data.matl, data.sch, data.nomDia)

    return data.d

def p(data, params, pipedb):
    """
    Calculates the pressure from flowrate

    Parameters
    ----------

    data : Data()
        The PSS calculation data object

    lossEqn

    """

    afl_ = afl(data, params, pipedb)

    logger.debugger("afl units: "+str(afl_.units))
    logger.debugger("dh units: "+str(data.dh.units))

    return afl(data, params, pipedb) + data.dh

def afl(data, params, pipedb, force = False):
    """Calculates the accumulated friction loss"""

    if data.afl is None or force == True:
        fl_ = fl(data, params, pipedb)
        data.afl = np.add.accumulate(fl_.magnitude)*fl_.units

    return data.afl

# def dp(data, force = False):
#     """Calculate pressure change in a pipe"""
#
#     data.p = hl(data) + dh(data)


def fl(data, params, pipedb, force=False):
    """Calculates the friction loss in pipe"""

    #TODO: Call to FlowHeadRelations must be modified for each additional
    #       derived class argument

    if data.fl is None or force == True:

        logger.debugger("d: "+str(data.d))
        logger.debugger("L: "+str(data.L))
        logger.debugger("C: "+str(data.C))
        C(data, params, pipedb)
        logger.debugger("C: "+str(data.C))


        fhrelation = FlowHeadRelationsFactory(d = data.d, L = data.L,
            roughness = roughness(data, params, pipedb), C = C(data, params, pipedb),
            pumps = data.pumps).create(params.lossEqn)
        data.fl = fhrelation(data.Q)
    return data.fl

def C(data, params, pipedb):
    """Returns the appropriate Hazen-Williams coefficient"""

    if data.C is None:
        read_pipedb(data, params, pipedb)
        data.C = np.array([pipedb.materials[mat].cfactor for mat in
            data.matl.flatten()])
    return data.C.reshape((-1,1))

def roughness(data, params, pipedb):
    """Returns the appropriate Darcy-Weisbach roughness coefficient"""

    if data.roughness is None:
        data = read_pipedb(data, params, pipedb)
        data.roughness = np.array([pipedb.materials[mat].roughness for mat in
        data.matl.flatten()], dtype="S24")
    return data.roughness

def L(data):
    """Get the pipe length from QGIS"""

    if data.L is None:

        distance = qgis.core.QgsDistanceArea()

        layer = qgis.utils.plugins["XPSS"].params.pipes_vlay

        lyr_crs = layer.crs()

        elps = QgsProject.instance().ellipsoid()
        elps_crs = QgsCoordinateReferenceSystem()
        elps_crs.createFromUserInput(elps)
        logger.debugger("Map Ellipsoid: "+str(elps))

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
        #logger.debugger("Converting from "+units.toString(units.DistanceMeters)+" to "+units.toString(calc_units)+".")
        #factor = QgsUnitTypes.fromUnitToUnitFactor(units.DistanceMeters, calc_units) ## TODO: Soft code
        #logger.debugger("Conversion factor: "+str(factor))

        for feature in features:
            #l_calc = distance.measureLength(feature.geometry())*factor
            #TODO: Soft code units
            l_calc = distance.measureLength(feature.geometry())
            len_.append(l_calc)#extract length from the QgsFeature
            logger.debugger(feature['id']+": "+str(l_calc))


        data.L = np.array(len_)*LengthUnits['m']

        logger.debugger("L: "+str(data.L))

    return data.L.reshape((-1,1))
