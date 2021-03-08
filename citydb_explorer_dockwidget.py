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

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsDataSourceUri,
    QgsMessageLog,
    QgsProject,
    QgsRectangle,
    QgsVectorLayer,
)
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import QSettings, pyqtSignal

from .attribute_dialog import AttributeDialog
from .db.postgresql import PostgreSQLInterface, PostgreSQLInterfaceException
from .tools.edit_generic import EditGenericAttributes

FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), "ui", "main.ui"))


class CityDbExplorerDockWidget(QtWidgets.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(CityDbExplorerDockWidget, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://doc.qt.io/qt-5/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.iface = iface
        self.db_interface = None

        # Populate database connection
        db_connections = self._postgres_connections()
        for item in db_connections:
            self.databaseConnections.addItem(item)

        # Event for the GUI.
        self.loadBuilding.clicked.connect(self.load_building)
        self.editAttribute.clicked.connect(self._edit_generic)
        self.connect.clicked.connect(self._database_connection)

        # Take track if the attribute edit tool is active.
        self.attribute_editor = None
        self.attribute_dialog = None

    def _postgres_connections(self):
        """
        Return the list of saved PostgreSQL connections.
        """

        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections")

        return [name for name in settings.childGroups()]

    def _connection_parameters(self) -> dict:
        """
        Read the connection parameters from the selected configuration
        and return a dict.
        """

        connection_name = self.databaseConnections.currentText()

        settings = QSettings()

        parameters = [
            settings.value(item)
            for item in [
                f"PostgreSQL/connections/{connection_name}/host",
                f"PostgreSQL/connections/{connection_name}/port",
                f"PostgreSQL/connections/{connection_name}/database",
                f"PostgreSQL/connections/{connection_name}/username",
                f"PostgreSQL/connections/{connection_name}/password",
            ]
        ]

        return dict(zip(["host", "port", "dbname", "username", "password"], parameters))

    def _database_connection(self):
        """
        Create a connection with the database. We will also
        check if the database is a 3DCity DB to print the version
        in the GUI.
        """

        connection_parameters = self._connection_parameters()

        # We try to build the connection to the database.
        try:
            self.db_interface = PostgreSQLInterface(connection_parameters)
        except PostgreSQLInterfaceException:
            self.dbVersion.setText("Error connecting to database.")
        else:
            # We have the connection. Now test if it is really a 3DCity DB
            version = self.db_interface.version
            self.srs = self.db_interface.srs
            extent = self.db_interface.extent
            if version != -1:
                self.dbVersion.setText(f"Connected. Current DB version is {version}.")
                # Set the project to the extent and srs of database
                QgsProject.instance().setCrs(
                    QgsCoordinateReferenceSystem.fromEpsgId(self.srs)
                )
                canvas = self.iface.mapCanvas()
                xmin, ymin, xmax, ymax = extent
                canvas.setExtent(QgsRectangle(xmin, ymin, xmax, ymax))

            else:
                # It is not a 3DCity DB. Reset the db_interface to None
                self.dbVersion.setText("Error. Current DB is not a 3DCity DB.")
                self.db_interface = None

    def load_building(self):
        """
        Load the buildings from the current extent.
        """

        if self.db_interface is None:
            return
        self._add_building_layer()

    def _create_buildings_uri(self) -> str:
        """Create a uri for the buildings in the current extent

        Returns:
            str: uri definition
        """

        connection_parameters = self._connection_parameters()
        extent = self.iface.mapCanvas().extent()
        limit = int(self.maxFeatures.text())

        sql_building = self.db_interface.sql_building(extent, self.srs, limit)

        uri = QgsDataSourceUri()
        uri.setConnection(*connection_parameters.values())

        uri.setUseEstimatedMetadata(True)

        uri.setDataSource("", "(" + sql_building + ")", "geom", "", "id")

        return uri.uri()

    def _add_building_layer(self):
        """"""
        uri = self._create_buildings_uri()
        virtual_layer = QgsVectorLayer(uri, "3D CityDB Buildings", "postgres")
        QgsProject.instance().addMapLayer(virtual_layer)

        # We need to update the uri on every zoom change
        self.iface.mapCanvas().extentsChanged.connect(self._update_layer_uri)

    def _update_layer_uri(self):
        """
        Update the layer uri
        """
        try:
            layer = QgsProject.instance().mapLayersByName("3D CityDB Buildings")[0]
        except IndexError:
            # TODO Remove signal
            pass
        else:
            uri = self._create_buildings_uri()
            layer.setDataSource(uri, "3D CityDB Buildings", "postgres")
            layer.triggerRepaint()

    def _edit_generic(self):
        """
        Edit generic attributes
        """
        layer = self.iface.activeLayer()
        canvas = self.iface.mapCanvas()

        if self.attribute_editor is not None:
            # Deactivating
            self.attribute_editor.deactivate()
            self.attribute_editor = None
        else:
            self.attribute_editor = EditGenericAttributes(canvas, layer)
            canvas.setMapTool(self.attribute_editor)
            self.attribute_editor.identifier.featureIdentified.connect(
                self._open_edit_generic
            )

    def _open_edit_generic(self, feature):
        """
        Open edit window
        """
        feature_id = feature.id()
        sql_query = """
                    WITH attribute_table AS (
                        SELECT
                        building.id as id,
                        generic.attrname,
                        generic.strval,
                        generic.realval,
                        generic.intval
                        FROM
                            citydb.building building
                        FULL JOIN
                            citydb.cityobject_genericattrib generic
                        ON building.id = generic.cityobject_id
                        WHERE building.id = {}
                        ORDER BY building.id, attrname
                    )

                    SELECT
                        id,
                        array_agg(attrname) as attributes,
                        array_agg(strval) as string_value,
                        array_agg(intval) as integer_value,
                        array_agg(realval) as real_value
                        from attribute_table group by id order by id;
                """.format(
            feature_id
        )

        with self.db_interface.connection.cursor() as cursor:

            cursor.execute(sql_query)
            query_results = cursor.fetchall()

            """ QgsMessageLog.logMessage(
                "Data from database: {}".format(query_results),
                tag="3D CityDB Plugin",
                level=Qgis.Info,
            ) """

            # TODO Fix it
            combination = zip(
                query_results[0][1],
                query_results[0][2],
                query_results[0][3],
                query_results[0][4],
            )

            self.attribute_dialog = AttributeDialog(combination, feature_id)
            self.attribute_dialog.buttonBox.clicked.connect(self._save_edit_generic)
            self.attribute_dialog.exec_()

    def _save_edit_generic(self, button):
        """
        Args:
            id ([type]): [description]
            combination ([type]): [description]
        """

        if button.text() == "Save":

            table = self.attribute_dialog.tableWidget
            feature_id = self.attribute_dialog.feature_id
            rows = table.rowCount()

            for row in range(rows):
                # values = [table.item(row, column).text() for column in range(columns)]
                attribute_name = table.item(row, 0).text()

                string_value = table.item(row, 1).text()

                try:
                    int_value = int(table.item(row, 2).text())
                except ValueError:
                    int_value = None

                try:
                    real_value = float(table.item(row, 3).text())
                except ValueError:
                    real_value = None
                connection = self.db_interface.connection

                cursor = connection.cursor()

                try:
                    QgsMessageLog.logMessage(
                        "Committing {} {} {} {} {}".format(
                            string_value,
                            int_value,
                            real_value,
                            feature_id,
                            attribute_name,
                        ),
                        tag="3D CityDB Plugin",
                        level=Qgis.Info,
                    )
                    cursor.execute(
                        """
                        UPDATE
                            citydb.cityobject_genericattrib
                        SET
                            (strval, intval, realval) = (%s, %s, %s)
                        WHERE
                            cityobject_id = %s
                        AND
                            attrname = %s
                    """,
                        (
                            string_value,
                            int_value,
                            real_value,
                            feature_id,
                            attribute_name,
                        ),
                    )
                except Exception:
                    QgsMessageLog.logMessage(
                        "Error executing query",
                        tag="3D CityDB Plugin",
                        level=Qgis.Warning,
                    )
                    connection.rollback()
                    self.attribute_dialog.statusText.setText("Error saving data.")
                else:
                    connection.commit()
                    QgsMessageLog.logMessage(
                        "Committed data", tag="3D CityDB Plugin", level=Qgis.Info
                    )
                    self.attribute_dialog.statusText.setText("Data saved.")

    def closeEvent(self, event):
        try:
            self.iface.mapCanvas().extentsChanged.disconnect(self._update_layer_uri)
        except TypeError:
            # TODO Fix
            pass

        # close connection to db
        self.db_interface.close_connection()

        self.closingPlugin.emit()
        event.accept()
