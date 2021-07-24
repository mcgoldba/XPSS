from XPSS.logger import Logger
from XPSS.pss.calc.driver import Driver

logger = Logger()

class DriverFactory(Driver):
    """ The factory class for creating drivers"""
    def __init__(self, dockwidget):
        super().__init__(dockwidget)
        self.dockwidget = dockwidget

    _registry = {}

    @classmethod
    def register(cls, key):
        def wrapper(func, **kwargs):
            cls._registry[key] = func
        return wrapper

    #@classmethod
    def create(self, key, **kwargs):
        driver = self.__class__._registry.get(key)
        if not driver:
            logger.error("Invalid driver key provided: "+str(key))
            raise ValueError(key)
        return driver(self.dockwidget, **kwargs)

    def run():
        pass
