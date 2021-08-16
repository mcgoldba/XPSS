from abc import ABC, abstractmethod

class FlowHeadRelations(ABC):
    def __init__(self, **kwargs):
        pass


from . import HazenWilliams
from . import DarcyWeisbach
