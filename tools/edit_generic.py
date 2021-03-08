#####################################################################################
# Copyright (C) 2021
# Chair of Geoinformatics
# Technical University of Munich, Germany
# https://www.gis.bgu.tum.de/
#
# This source is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# This code is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# The 3D City Database is jointly developed with the following cooperation partners:
#
# virtualcitySYSTEMS GmbH, Berlin <http://www.virtualcitysystems.de/>
# M.O.S.S. Computer Grafik Systeme GmbH, Taufkirchen <http://www.moss.de/>
#
#####################################################################################


from qgis.gui import QgsMapTool, QgsMapToolEmitPoint, QgsMapToolIdentifyFeature
from qgis.PyQt.QtCore import Qt


class EditGenericAttributes(QgsMapToolEmitPoint):
    """
    Tool to edit generic attributes by clicking on
    the map.
    """

    def __init__(self, canvas, layer):

        QgsMapToolEmitPoint.__init__(self, canvas)
        self.canvas = canvas
        self.layer = layer

        self.identifier = QgsMapToolIdentifyFeature(canvas, layer)

        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, event):
        feature = self.identifier.identify(
            event.x(), event.y(), self.identifier.TopDownStopAtFirst
        )[0]
        self.identifier.featureIdentified.emit(feature.mFeature)

    def deactivate(self):
        QgsMapTool.deactivate(self)
        self.deactivated.emit()
