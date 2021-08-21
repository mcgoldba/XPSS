import numpy as np
import math

from . import NomDia
from .nomdiafactory import NomDiaFactory

from XPSS.pss.db.units import LengthUnits

from XPSS.logger import Logger


logger = Logger(debug=False)

@NomDiaFactory.register('From flow rate')
class FromQ(NomDia):
    def __init__(self, data, params, pipedb, pipe_fts):
        super().__init__(data, params, pipedb, pipe_fts)
        self.Q = data.Q
        self.nEDU = data.nEDU
        self.n = data.n

    def get(self):
        """
        Calculate the pipe nominal diameter based on flowrate

        Parameters
        ----------
        Q : np.array_like
            The flowrates in each pipe.

        minV : float
            The minimum allowable fluid average velocity

        maxV : float
            The maximum allowable fluid average velocity

        material : str
            The material for each pipe.

        Returns
        -------

        nomDia : np.array_like(float)
            nominal diameter for each pipe

        matl : np.array_like(string)
            material for each pipe

        sch : np.array_like(string)
            schedule of each pipe
        """
        #TODO: Optimize (prevent iterating through array item by item)
        #TODO: update to allow for different materials and schedules for each pipe

        Q = self.Q
        minV = self.params.minV
        maxV = self.params.maxV
        material = self.params.pipeMaterial
        latMaterial = self.params.latConnMaterial
        schedule = self.params.pipeSchedule
        latSchedule = self.params.latConnPipeSch
        latDia = self.params.latConnDia

        #TODO:  Handle latDia units

        pipedb = self.pipedb

        logger.debugger("material: "+str(material))

        if isinstance(material, str):
            latID = pipedb.get(material, schedule, latDia)
            diadb = pipedb.get(material, schedule).diameters
            units = LengthUnits[pipedb.get(material, schedule).baseunits]

            logger.debugger("units: "+str(units))
        else:
            logger.error("Material specification must be a string value")

        if Q is None:
            logger.error("Flowrate variable is not availbale.")

        nomDia = np.empty(Q.shape)
        matl = np.empty(Q.shape, dtype="S24")
        sch = np.empty(Q.shape, dtype="S24")

        for i in range(self.n):
            nomDia[i] = latDia
            matl[i] = latMaterial
            sch[i] = latSchedule
            if not self.nEDU[i]: #if not end node, calculate diameter
                matl[i] = material
                sch[i] = schedule
                dmin = self._dstar(Q[i], minV)
                dmax = self._dstar(Q[i], maxV)
                for nd in diadb.keys():
                    inDia = (float(diadb[nd])*units)#.to_base_units().magnitude
                    logger.debugger("dia: "+str(inDia))
                    logger.debugger("dmin: "+str(dmin))
                    if inDia > dmin and inDia < dmax:
                        nomDia[i] = diadb[nd]
                        break
                if not nomDia[i]:
                    logger.error("Could not find suitable diameter for"\
                                 " pipe index "+str(i))
            logger.debugger(str(matl))

        return nomDia*units, matl.astype(str), sch.astype(str)

    def _dstar(self,q,v):
        """
        Calculates the pipe diameter based on flowrate and velocity

        Parameters
        ----------

        q : array_like(float)
            Flowrate

        v : array_like(float)
            Pipe average velocity
        """
        return np.sqrt((4/math.pi)*q/v)
