from XPSS.pss.calc.nomdia import NomDia
from XPSS.pss.calc.nomdia.nomdiafactory import NomDiaFactory

@NomDiaFactory.register('From QGIS layer')
class FromQGIS(NomDia):
    def __init__(self, data, params, pipedb):
        super().__init__(data, params, pipedb)

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


        material = self.lMaterial
        latMaterial = self.latMaterial
        sch = self.lSch
        latSch = self.latSch
        latDia = float(self.latDia)

        pipedb = self.dockwidget.pipedb

        if isinstance(material, str):
            latID = pipedb.get(material, sch, latDia)
            diadb = pipedb.get(material, sch).diameters
            units = LengthUnits[pipedb.get(material, sch).baseunits]

            logger.debugger("units: "+str(units))
        else:
            logger.error("Material specification must be a string value")

        #nomDia = np.empty((self.n,1))

        logger.debugger("pipeProps:\n"+str(pipeProps))

        nomDia = self.pipeProps["Nominal Diameter"]

        for i in range(self.n):
            if not self.nEDU[i]: #if not end node, calculate diameter

                nomDia[i] = diadb[nd]
                if not nomDia[i]:
                    logger.error("Could not find suitable diameter for"\
                                 " pipe index "+str(i))

        return nomDia
