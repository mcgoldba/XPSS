import pint

from ..operations import dsConn

from XPSS.logger import Logger

logger = Logger(debug=False)

ureg = pint.UnitRegistry()

class Report:
    def __init__(self, pssvars):
        self.dockwidget = pssvars.dockwidget
        self.pipeID = pssvars.pipeProps["Pipe ID"]
        self.downstreamConn = dsConn(pssvars)
        self.nEDU = pssvars.nEDU
        self.nAEDU = pssvars.nAEDU
        self.nOpEDU = pssvars.nOpEDU
        self.Q = pssvars.Q
        self.d = pssvars.d
        self.v = pssvars.v
        self.L = pssvars.L

        self.units = {
        'length': pssvars.dockwidget.cbo_rpt_units_pipe_length.currentText(),
        'diameter': pssvars.dockwidget.cbo_rpt_units_diameter.currentText(),
        'pressure': pssvars.dockwidget.cbo_rpt_units_pressure.currentText(),
        'flow': pssvars.dockwidget.cbo_rpt_units_flow.currentText(),
        'velocity': pssvars.dockwidget.cbo_rpt_units_velocity.currentText()
        }

    def create(self):
        logger.progress("Report not created.  Need more code!")

    def convert_units(self, value):
        """
        Convert from the internal calculation units (SI) to user specified,
        display units
        """
