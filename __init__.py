# -*- coding: utf-8 -*-
"""
/***************************************************************************
XPSS
                                 A QGIS plugin
 This plugin perform pressure sewer system calculations within QGIS.
                             -------------------
        begin                : 2021-07-21
        git sha              : $Format:%H$
        copyright            :
        email                : mcgoldba@gmail.com

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load XPSS class from file XPSS.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .xpss import XPSS
    return XPSS(iface)
