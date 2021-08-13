import configparser
from enum import Enum, auto
import os
import pint

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
    "m^3/s": ureg.meter**3/ureg.second
    }

VelocityUnits = {
    "ft/s": ureg.foot/ureg.second,
    "m/s": ureg.meter/ureg.second
    }
