import math
from XPSS.pss.calc.opedumethod import OpEduMethod
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory

@OpEduMethodFactory.register("EPA")
class EPA(OpEduMethod):
    def __init__(self, n, a, b):
        super().__init__(n)
        self.a = float(a)
        self.b = float(b)

    def calc(self):
        return math.ceil(self.a*self.n +self.b)
