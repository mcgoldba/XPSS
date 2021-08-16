import math
import numpy as np

from XPSS.pss.calc.opedumethod import OpEduMethod
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory

from XPSS.pss.db.units import FlowUnits


@OpEduMethodFactory.register("EPA")
class EPA(OpEduMethod):
    def __init__(self, params, n):
        super().__init__(params, n)
        self.a = float(params.epaA)
        self.b = float(params.epaB)
        self.Q = params.flowrate.to(FlowUnits["gpm"]).magnitude

    def calc(self):
        return np.max(((self.a*self.n +self.b)/self.Q).astype(int), 1).reshape(-1,1)
