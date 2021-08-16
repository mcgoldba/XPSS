from abc import abstractmethod
from XPSS.logger import Logger
from XPSS.pss.calc.opedumethod import OpEduMethod

logger = Logger()

class OpEduMethodFactory(OpEduMethod):
    def __init__(self, params, n):
        super().__init__(params, n)

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key, **kwargs):
        opedumethod = self.__class__.registry.get(key)
        if not opedumethod:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        return opedumethod(self.params, self.n)

    def calc(self, **kwargs):
        pass
