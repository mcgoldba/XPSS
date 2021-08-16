from XPSS.logger import Logger
from XPSS.pss.calc.flowheadrelations import FlowHeadRelations

logger = Logger()

class FlowHeadRelationsFactory(FlowHeadRelations):
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)
        self.kwargs = kwargs

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key):
        fhrelation = self.__class__.registry.get(key)
        if not fhrelation:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        #return fhrelation(self.Cf, self.r, **kwargs)
        return fhrelation(**self.kwargs)
