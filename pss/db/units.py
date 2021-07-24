import configparser
from enum import Enum, auto
import os
import pint

from XPSS.logger import Logger

#from XPSS.utils import get_root_dir

# logger = Logger(debug=True)
#
# configfile = os.path.join(get_root_dir(), 'config.ini')
#
# logger.debugger('configfile: '+str(configfile))
#
# config = configparser.ConfigParser()
# config.read(configfile)

ureg = pint.UnitRegistry()

LengthUnits = [ureg.inch, ureg.mm, ureg.ft, ureg.meter]

FlowUnits = [ureg.gallon/ureg.minute, ureg.litre / ureg.minute,
              ureg.meter**3/ureg.second]

# class LengthUnits(Enum):
#     in = auto()
#     mm = auto()
#     ft = auto()
#     m = auto()
#
#
# class FlowUnits(Enum):
#     gpm = auto()
#     lps = auto()
#     m3s = auto()
