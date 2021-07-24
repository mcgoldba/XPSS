from abc import ABC, abstractmethod
from XPSS.pss.calc import Calc

class OpEduMethod(Calc, ABC):
    def __init__(self, n, **kwargs):
        self.n = int(n)

    @abstractmethod
    def calc(self):
        pass

from . import epa
from . import rational
