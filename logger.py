from qgis.core import QgsMessageLog
from qgis.utils import iface

class Logger:
    def __init__(self, debug=False):
        self.debug = debug

    def progress(self, message):
        QgsMessageLog.logMessage(message, tag="XPSS Progress Log", level=0)

    def warning(self, message):
        QgsMessageLog.logMessage(message, tag="XPSS Progress Log", level=1)

        iface.messageBar().pushWarning("XPSS Warning", message)

    def error(self, message, stop=True):
        QgsMessageLog.logMessage(message, tag="XPSS Progress Log", level=2)

        iface.messageBar().pushCritical("XPSS Error", message)

        if stop is True:
            raise Exception(message)

    def debugger(self, message):
        print(self.debug)
        if self.debug is True:
            QgsMessageLog.logMessage(message, tag="XPSS Progress Log", level=0)
