from XPSS.logger import Logger
from XPSS.pss.calc.nomdia import NomDia

logger = Logger()

class NomDiaFactory(NomDia):
    def __init__(self, pssvars):
        super().__init__(pssvars)
        self.dockwidget = pssvars.dockwidget
        self.pssvars = pssvars

    registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls.registry[key] = func
        return wrapper

    def create(self, key, **kwargs):
        nomdiamethod = self.__class__.registry.get(key)
        if not nomdiamethod:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        return nomdiamethod(self.pssvars)

    def get(self):
        pass
