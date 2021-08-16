from abc import ABC, abstractmethod

class NomDia(ABC):
    def __init__(self, data, params, pipedb):
        self.data = data
        self.params = params
        self.pipedb = pipedb

    @abstractmethod
    def get(self):
        pass

from . import fromQ
from . import fromQGIS
