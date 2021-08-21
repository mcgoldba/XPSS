import pint

from ..calc.operations import dsConn

from XPSS.logger import Logger

logger = Logger(debug=False)

ureg = pint.UnitRegistry()

class Report:
    def __init__(self, pssvars):
        #self.dockwidget = pssvars.dockwidget
        self.pipeID = pssvars.pipeProps["Pipe ID"]
        self.downstreamConn = dsConn(pssvars.data)
        self.nEDU = pssvars.data.nEDU
        self.nAEDU = pssvars.data.nAEDU
        self.nOpEDU = pssvars.data.nOpEDU
        self.Q = pssvars.data.Q
        self.d = pssvars.data.d
        self.v = pssvars.data.v
        self.L = pssvars.data.L


    def create(self):
        logger.progress("Report not created.  Need more code!")

    def convert_units(self, value):
        """
        Convert from the internal calculation units (SI) to user specified,
        display units
        """
