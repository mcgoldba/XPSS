from XPSS.logger import Logger
from XPSS.pss.calc.flowheadrelations import FlowHeadRelations

logger = Logger()

class FlowHeadRelationsFactory(FlowHeadRelations):
    def __init__(self, pssvars):
        self.pssvars = pssvars

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key, **kwargs):
        fhrelation = self.__class__.registry.get(key)
        if not fhrelation:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        #return fhrelation(self.Cf, self.r, **kwargs)
        return fhrelation(self.pssvars, **kwargs)
