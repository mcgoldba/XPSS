#ref: https://realpython.com/factory-method-python/
from abc import ABC, abstractmethod
from XPSS.pss.calc import Calc

class Driver(Calc, ABC):
    def __init__(self, dockwidget):
        super().__init__(dockwidget)
        self.nEDU = None

    @abstractmethod
    def run(self, **kwargs):
        pass

    # @classmethod
    # @abstractmethod
    # def create(cls, key, **kwargs):
    #     pass

#from .driverfactory import DriverFactory
from .constantflow import ConstantFlow
from .centrifugal import Centrifugal
