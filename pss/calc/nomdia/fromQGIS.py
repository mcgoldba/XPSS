import numpy as np

from XPSS.pss.calc.nomdia import NomDia
from XPSS.pss.calc.nomdia.nomdiafactory import NomDiaFactory

from XPSS.pss.db.units import LengthUnits

@NomDiaFactory.register('From QGIS layer')
class FromQGIS(NomDia):
    def __init__(self, data, params, pipedb, pipe_fts):
        super().__init__(data, params, pipedb, pipe_fts)

    def get(self, **ignored):
        """
        Read pipe diameters from the QGIS "Pipe" layer

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
        """
        #TODO: update to allow for different materials and schedules for each pipe
        #TODO:  allow for different length units

        nomDia = np.array(self.pipe_fts['diameter']).reshape(-1,1)

        units = LengthUnits[self.pipe_fts['diameter_units'][0]] #TODO Assumes all pipes are same units

        material = np.array(self.pipe_fts['material']).reshape(-1,1)

        schedule = np.full(material.shape, "DR11") #TODO: Add as QGIS attribute

        return nomDia*units, material, schedule
