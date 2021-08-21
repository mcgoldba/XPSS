from abc import ABC, abstractmethod

class NomDia(ABC):
    def __init__(self, data, params, pipedb, pipe_fts):
        self.data = data
        self.params = params
        self.pipedb = pipedb
        self.pipe_fts = pipe_fts

    @abstractmethod
    def get(self):
        pass

from . import fromQ
from . import fromQGIS
