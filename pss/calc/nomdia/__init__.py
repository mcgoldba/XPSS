from abc import ABC, abstractmethod
from XPSS.pss.calc import Calc

class NomDia(Calc, ABC):
    def __init__(self, pssvars):
        super().__init__(pssvars.dockwidget)

    @abstractmethod
    def get(self):
        pass

from . import fromQ
from . import fromQGIS
