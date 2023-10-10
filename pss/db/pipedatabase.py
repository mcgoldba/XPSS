import csv
from enum import Enum, auto
import re
import numpy as np
#from .units import LengthUnits

from XPSS.logger import Logger

logger = Logger(debug=False)

from pint import UnitRegistry

ureg = UnitRegistry()

from XPSS.pss.db.units import LengthUnits

class PipeDatabase:
    def __init__(self):
        self.materials = {}

    def load(self, pipe_dia_filepath, pipe_rgh_filepath):

        nPipeMatl = 0
        # Read in pipe roughness database
        with open(pipe_rgh_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            for row in reader:
                if (len(row) == 4 and all([v is not "" for v in row])):
                    nPipeMatl+=1
                    self.materials.update(
                        {row[0]: PipeMaterial(row[0], row[1],
                                              row[2],row[3])}
                        )
        if not nPipeMatl:
            logger.error("Invalid pipe roughness database specification")

        nPipeDia = 0
        # Read in pipe diameters database
        with open(pipe_dia_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            for row in reader:
                if (len(row) == 5 and all([v is not "" for v in row])):
                    nPipeDia+=1
                    [matl, sch, nom_dia, in_dia, unit] = row
                    logger.debugger("schedule: "+str(sch))
                    try:
                        material = PipeMaterial.get(matl)
                    except ValueError:
                        logger.error("Pipe material '"+str(matl)+"' not found in "\
                                     "pipe roughness database")
                    if sch not in material.schedules.keys():
                        logger.debugger("Adding pipe schedule "+str(sch))
                        material.schedules.update({sch: PipeSchedule(sch,
                                                                   unit)})
                    base_unit = material.schedules[sch].baseunits
                    material.schedules[sch].diameters.update(
                        {float(nom_dia)*ureg[unit].to(base_unit).magnitude:
                         float(in_dia)*ureg[unit].to(base_unit).magnitude}
                        )

        if not nPipeDia:
            logger.error("Invalid pipe diameter database specification.")

        return self


    def _add_pipe(material, schedule, nominal_dia, inner_dia):
        try:
            material = PipeMaterial.get(material)
        except ValueError:
            logger.error("Pipe material '"+str(material)+"' not found in "\
                         "pipe roughness database")
    def get(self, material, schedule=None, nomDia=None):
        """
        Convenience function to return the appropriate database object based on
        the provided inputs.

        Inputs                    | Returns
        --------------------------|---------------
        material                  | PipeMaterial
        material, schedule        | PipeSchedule
        material schedule, nomDia | inner_diameter

        """


        dim_error = "Inconsistent dimensions."

        if isinstance(material, str):
            if schedule and nomDia:
                return self.materials[material].schedules[schedule].\
                                diameters[nomDia]
            elif schedule:
                return self.materials[material].schedules[schedule]
            else:
                return self.materials[material]

        elif isinstance(material, np.ndarray) and\
        isinstance(schedule, np.ndarray) and nomDia is not None:
            try: #Convert to baseunits if nomDia is dimensioned
                nomDiaUnits = nomDia.units
                baseunits_ = self.material[0][0].schedules[schedule[0][0]].baseunits
                nomDia = nomDia.to(baseunits_)
                nomDia = nomDia.magnitude
            except:
                pass
            if material.shape == schedule.shape == nomDia.shape:
                #convert string fron byte like object
                material = material.astype(str)
                schedule = schedule.astype(str)
                nomDia = nomDia.astype(float)

                logger.debugger("diameters: "+str(self.materials[material[0][0]].schedules[schedule[0][0]].diameters.keys()))

                # return np.array([self.materials[mat].schedules[sch].\
                #             diameters[float(d)]*LengthUnits[
                #             self.materials[mat].schedules[sch].baseunits]
                #             for mat, sch, d in np.stack(
                #             (material.flatten(), schedule.flatten(),
                #             nomDia.flatten()), axis=1)])
                d =  np.array([self.materials[mat].schedules[sch].\
                            diameters[float(d)]
                            for mat, sch, d in np.stack(
                            (material.flatten(), schedule.flatten(),
                            nomDia.flatten()), axis=1)])

                logger.debugger('diameters: '+str(d))
                #TODO: assumes all values have same base dimensions
                #       This is a limitation with the pint library (I think)
                d = d.reshape((-1,1))
                d *= LengthUnits[self.materials[material[0][0]].\
                    schedules[schedule[0][0]].baseunits]
                logger.debugger('diameters: '+str(d))
                return d
            else:
                logger.error(dim_error)
        elif isinstance(material, np.ndarray) and\
        isinstance(schedule, np.ndarray):
            if material.shape == schedule.shape:
                return np.array([self.materials[mat].schedules[sch] for
                    mat, sch in zip(material, schedule)])
            else:
                logger.error(dim_error)
        else:
                return np.array([self.materials[mat] for mat in material])

    def __repr__(self):
        return str("PipeDatabase("+str(self.materials)+")")


class PipeMaterial:

    instances = []

    def __init__(self, name, cfactor, roughness, roughness_unit):
        self.name = str(name)
        self.cfactor = float(cfactor)
        self.roughness = float(roughness)
        self.roughnessunit = roughness_unit

        if LengthUnits[self.roughnessunit].dimensionality !=\
            ureg.meter.dimensionality:
            logger.error("Invalid unit specification in database file: "+
                         str(self.roughnessunit))

        self.instances.append(self)

        self.schedules = {}

    def __repr__(self):
        return str("PipeMaterial("+str(self.name)+", "+
                   str(self.cfactor)+", "+str(self.roughness)+", "+
                   str(self.roughnessunit)+", "+str(self.schedules)+")")

    @classmethod
    def get(cls, name):
        for instance in cls.instances:
            if instance.name == name:
                return instance
        return ValueError(name)


class PipeSchedule:
    def __init__(self, name, baseunits):
        self.name = str(name)
        self.baseunits = baseunits
        self.diameters = {}

        if LengthUnits[self.baseunits].dimensionality !=\
            ureg.meter.dimensionality:
            logger.error("Invalid unit specification in database file: "+
                         str(self.baseunit))

    def __repr__(self):
        return str("PipeSchedule("+str(self.name)+", "+str(self.baseunits)+
                ", "+str(self.diameters)+")")
