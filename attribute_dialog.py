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


import os

from qgis.PyQt.QtWidgets import QDialog, QTableWidgetItem
from qgis.PyQt import uic
from qgis.PyQt import QtCore

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "ui/attribute.ui")
)


class AttributeDialog(QDialog, FORM_CLASS):
    """
    Dialog to edit generic attributes
    """

    def __init__(self, combination, feature_id, parent=None):
        super(AttributeDialog, self).__init__(parent)
        QDialog.__init__(self)
        self.setupUi(self)
        self._populate_attributes(combination)

        # The id of the feature we are going to edit
        self.feature_id = feature_id

    def _populate_attributes(self, combination):
        """
        Populate the attributes
        """

        data = list(combination)

        self.tableWidget.setRowCount(len(data))

        for row_index, row in enumerate(data):
            for index in range(4):
                item = QTableWidgetItem(str(row[index]))
                if index == 0:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                self.tableWidget.setItem(row_index, index, item)
        self.tableWidget.resizeColumnsToContents()
