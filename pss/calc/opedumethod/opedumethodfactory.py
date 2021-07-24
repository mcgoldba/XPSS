from XPSS.logger import Logger
from XPSS.pss.calc.opedumethod import OpEduMethod

logger = Logger()

class OpEduMethodFactory(OpEduMethod):

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key, **kwargs):
        opedumethod = self.__class__.registry.get(key)
        if not opedumethtod:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        return opedumethod(**kwargs)
