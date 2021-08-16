from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *

import qgis.utils

from .nomdia.nomdiafactory import NomDiaFactory

from XPSS.logger import Logger

logger = Logger(debug=False)

def dsConn(pssvars):
    pipeID = pssvars.pipeProps["Pipe ID"]

    dsConn = pssvars.pipeProps["Pipe ID"].to_numpy().T&pssvars.A
    dsConn[0] = self.res

    return dsConn

def read_pipedb(data, params, pipedb, force=False):

    logger.debugger("nomDia: "+str(data.nomDia))
    logger.debugger("matl: "+str(data.matl))
    logger.debugger("sch: "+str(data.sch))

    if (any(item is None for item in [data.nomDia, data.matl, data.sch]) or
        force == True):

        logger.debugger("Populating pipe properties")

        nomdiamethod = NomDiaFactory(data, params, pipedb).create(params.nomDiaMethod)

        [data.nomDia, data.matl, data.sch] = nomdiamethod.get()

    return data
