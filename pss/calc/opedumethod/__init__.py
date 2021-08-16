from abc import ABC, abstractmethod
from XPSS.pss.calc import Calc

class OpEduMethod(Calc, ABC):
    def __init__(self, params, n):
        self.params = params
        self.n = n

    #nOpEDU = None

    @abstractmethod
    def calc(self):
        pass

from . import epa
from . import rational
