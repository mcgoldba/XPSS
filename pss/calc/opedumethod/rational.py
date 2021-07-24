import math
from XPSS.pss.calc.opedumethod import OpEduMethod
from XPSS.pss.calc.opedumethod.opedumethodfactory import OpEduMethodFactory

@OpEduMethodFactory.register("Rational")
class Rational(OpEduMethod):
    def __init__(self, n):
        super().__init__(n)

    def calc(self):
        return 0
