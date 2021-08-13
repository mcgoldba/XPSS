from ..operations import dsConn
from ..systemops import Q, d, v, L

class Report:
    def __init__(self, pssvars):
        self.dockwidget = pssvars.dockwidget
        self.pipeID = pssvars.pipeProps["Pipe ID"]
        self.downstreamConn = dsConn(pssvars)
        self.nEDU = pssvars.nEDU
        self.nAEDU = pssvars.nAEDU
        self.nOpEDU = pssvars.nOpEDU
        self.Q = Q(pssvars)
        self.d = d(pssvars)
        self.v = v(pssvars)
        self.len = L(pssvars)
