#ref: https://realpython.com/factory-method-python/
from abc import ABC, abstractmethod
from XPSS.pss.calc import Calc

class Solver(Calc, ABC):
    def __init__(self, params, pipedb, data):
        super().__init__(params, pipedb, data)

    @abstractmethod
    def run(self, **kwargs):
        pass

    # @classmethod
    # @abstractmethod
    # def create(cls, key, **kwargs):
    #     pass

#from .solverfactory import DriverFactory
from .constantflow import ConstantFlow
from .centrifugal import Centrifugal
