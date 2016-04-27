# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Parametric_Draw
                                 A QGIS plugin
 allow to draw parametric objects
                             -------------------
        begin                : 2016-04-27
        copyright            : (C) 2016 by Ville de Lausanne
        email                : cgil@lausanne.ch
        git sha              : $Format:%H$
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
    """Load Parametric_Draw class from file Parametric_Draw.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .parametric_draw import Parametric_Draw
    return Parametric_Draw(iface)
