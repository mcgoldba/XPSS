import csv
from enum import Enum, auto
import re
#from .units import LengthUnits

from XPSS.logger import Logger


from pint import UnitRegistry

logger = Logger(debug=True)

ureg = UnitRegistry()

class PipeDatabase:
    def __init__(self):
        self.materials = {}

    def load(self, pipe_dia_filepath, pipe_rgh_filepath):

        with open(pipe_rgh_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            for row in reader:
                if (len(row) == 4 and all([v is not "" for v in row])):

                    self.materials.update(
                        {row[0]: PipeMaterial(row[0], row[1],
                                              row[2],ureg[row[3]])}
                        )


        with open(pipe_dia_filepath, newline='') as csvfile:
            reader = csv.reader(csvfile)
            headers = next(reader, None)
            for row in reader:
                if (len(row) == 4 and all([v is not "" for v in row])):
                    [matl, sch, nom_dia, in_dia, unit] = row
                    try:
                        material = PipeMaterial.get(matl)
                    except ValueError:
                        logger.error("Pipe material '"+str(matl)+"' not found in "\
                                     "pipe roughness database")
                    if sch not in material.schedules.keys():
                        material.schedules.update({sch: PipeSchedule(sch,
                                                                   ureg[unit])})
                    base_unit = material.schedules[sch].base_unit
                    material.schedules[sch].diameters.update(
                        {float(nom_dia)*ureg[unit].to(base_unit):
                         float(in_dia)*ureg[unit].to(base_unit)}
                        )
        return self


    def _add_pipe(material, schedule, nominal_dia, inner_dia):
        try:
            material = PipeMaterial.get(material)
        except ValueError:
            logger.error("Pipe material '"+str(material)+"' not found in "\
                         "pipe roughness database")

    def __repr__(self):
        return str("PipeDatabase("+str(self.materials)+")")


class PipeMaterial:

    instances = []

    def __init__(self, name, cfactor, roughness, roughness_unit):
        self.name = str(name)
        self.cfactor = float(cfactor)
        self.roughness = float(roughness)
        self.roughness_unit = roughness_unit

        if self.roughness_unit.dimensionality != ureg.meter.dimensionality:
            raise TypeError(self.roughness_unit)

        self.instances.append(self)

        self.schedules = {}

    @classmethod
    def get(cls, name):
        for instance in cls.instances:
            if instance.name == name:
                return instance
        return ValueError(name)


class PipeSchedule:
    def __init__(self, name, baseunits):
        self.name = str(name)
        self.baseunits = None
        self.diameters = {}

# class PipeDiameters:
#     def __init__(self, nominal_dia=[], inner_dia=[]):
#         self.diameters = {}
#         self.units = LengthUnits()
#
#         for nd, id in zip(nominal_dia, inner_dia):
#             self.diameters.update({nd: id})
#
#     def __repr__(self):
#         return str("PipeDiameters("+str(self.units)+", "+str(self.diameters))
