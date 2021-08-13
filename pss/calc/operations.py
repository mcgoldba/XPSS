from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qgis.core import *

import qgis.utils


def dsConn(pssvars):
    pipeID = pssvars.pipeProps["Pipe ID"]

    dsConn = pssvars.pipeProps["Pipe ID"].to_numpy().T&pssvars.A
    dsConn[0] = self.res

    return dsConn

def read_pipedb(pssvars, force=False):

    if not any([pssvars.nomDia, pssvars.matl, pssvars.sch]) or force == True:

        nomdiamethod = NomDiaFactory(pssvars).create(
            pssvars.dockwidget.cbo_dia_method.currentText())

        [pssvars.nomDia, pssvars.matl, pssvars.sch] = nomdiamethod.get()
