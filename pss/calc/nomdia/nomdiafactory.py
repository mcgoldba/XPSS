from XPSS.logger import Logger
from XPSS.pss.calc.nomdia import NomDia

logger = Logger()

class NomDiaFactory(NomDia):
    def __init__(self, data, params, pipedb, pipe_fts):
        super().__init__(data, params, pipedb, pipe_fts)

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
        return nomdiamethod(self.data, self.params, self.pipedb, 
                            self.pipe_fts)

    def get(self):
        pass
