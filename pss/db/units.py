import configparser
from enum import Enum, auto
import os
import pint
import copy

from XPSS.logger import Logger

ureg = pint.UnitRegistry()

LengthUnits = {
    "in": ureg.inch,
    "mm": ureg.mm,
    "ft": ureg.ft,
    "m": ureg.meter
    }

FlowUnits = {
    "gpm": ureg.gallon/ureg.minute,
    "lpm": ureg.litre / ureg.minute,
    "m^3/s": ureg.meter**3/ureg.second,
    "gpm (Imp)": ureg.imperial_gallon/ureg.minute
    }

VelocityUnits = {
    "ft/s": ureg.foot/ureg.second,
    "m/s": ureg.meter/ureg.second
    }

PressureUnits = {
    "ft": ureg.foot_H2O,
    "m": ureg.meter*ureg.water*ureg.g_0,
    "psi": ureg.pound/(ureg.inch)**2,
    "Pa": ureg.pascal
}

MetricSystem = {
    "length": "m",
    "diameter": "mm",
    "flow": "lpm",
    "pressure": "m",
    "velocity": "m/s"
}

USSystem = {
    "length": "ft",
    "diameter": "in",
    "flow": "gpm",
    "pressure": "ft",
    "velocity": "ft/s"
}

ImperialSystem = copy.deepcopy(USSystem)
ImperialSystem.update({"flow": "gpm (Imp)"})
