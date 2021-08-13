from abc import ABC, abstractmethod

class FlowHeadRelations(ABC):
    def __init__(self, pssvars):
        pass


from . import HazenWilliams
from . import DarcyWeisbach
