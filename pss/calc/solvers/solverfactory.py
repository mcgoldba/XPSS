from XPSS.logger import Logger
from XPSS.pss.calc.solvers import Solver

logger = Logger()

class SolverFactory(Solver):
    """ The factory class for creating drivers"""
    def __init__(self, params, pipedb, data=None):
        super().__init__(params, pipedb, data)

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key, **kwargs):
        solver = self.__class__.registry.get(key)
        if not solver:
            logger.error("Invalid solver key provided: "+str(key))
            raise ValueError(key)
        return solver(self.params, self.pipedb, data=self.data)

    def run():
        pass
