import math
import numpy as np

from XPSS.pss.calc.opedumethod import OpEduMethod
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory



@OpEduMethodFactory.register("EPA")
class EPA(OpEduMethod):
    def __init__(self, dockwidget, n):
        super().__init__(dockwidget, n)
        self.a = float(dockwidget.txt_epa_a.text())
        self.b = float(dockwidget.txt_epa_b.text())
        self.Q = float(dockwidget.txt_flowrate.text())

    def calc(self):
        return np.max(((self.a*self.n +self.b)/self.Q).astype(int), 1).reshape(-1,1)
