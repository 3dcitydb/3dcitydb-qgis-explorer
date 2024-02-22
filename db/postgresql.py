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
import warnings
from psycopg2 import Error, InterfaceError, OperationalError, connect


class PostgreSQLInterfaceException(Exception):
    """
    Exception for PostgreSQLInterface
    """


class PostgreSQLInterface:
    """
    PostgreSQL interface to 3D CityDB.
    """

    def __init__(self, connection_dict):
        """Create the connection to the database

        Args:
            connection_dict (dict): [description]
        """

        connection_string = "host={0} dbname={1} user={2} password={3} port={4}".format(
            connection_dict["host"],
            connection_dict["dbname"],
            connection_dict["username"],
            connection_dict["password"],
            connection_dict["port"],
        )
        try:
            self.connection = connect(connection_string)
        except OperationalError:
            raise PostgreSQLInterfaceException("Error connecting to database")

    def count_building(self, extent: dict, epsg: int) -> int:
        """"""

        with self.connection.cursor() as cursor:

            cursor.execute(
                """
                    SELECT
                        COUNT(*)
                    FROM
                        citydb.cityobject
                    WHERE
                        objectclass_id = 26
                    AND
                        ST_Intersects(envelope,ST_MakeEnvelope(%s, %s, %s, %s, %s))
                """,
                [
                    extent.xMinimum(),
                    extent.xMaximum(),
                    extent.yMinimum(),
                    extent.yMaximum(),
                    epsg,
                ],
            )
            (count,) = cursor.fetchone()

            return count

    def sql_building(self, extent: dict, epsg: int, limit=None) -> str:
        """
        SQL to fetch the buildings
        """

        return """
            WITH geometry_data AS (SELECT
                b.id as id, sg.geometry AS single_geom
            FROM
                citydb.surface_geometry sg
            LEFT JOIN
                citydb.thematic_surface ts ON ts.lod2_multi_surface_id = sg.root_id
            LEFT JOIN
                citydb.building b ON ts.building_id = b.building_root_id
            WHERE
                sg.geometry IS NOT NULL
                AND
                ts.lod2_multi_surface_id IS NOT NULL
                AND
                ST_Intersects(sg.geometry, ST_MakeEnvelope({0}, {1}, {2}, {3}, {4}))
            LIMIT {5})

            SELECT id, st_collect(single_geom) as geom
            FROM
                geometry_data
            WHERE
                id IS NOT NULL
            GROUP BY id
        """.format(
            extent.xMinimum(),
            extent.yMinimum(),
            extent.xMaximum(),
            extent.yMaximum(),
            epsg,
            limit,
        )

    @property
    def version(self):
        """
        Return
        """

        SQLv4 = """
            SELECT version FROM citydb_pkg.citydb_version()
        """

        SQLv3 = """
            SELECT citydb_version()
        """

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(SQLv4)
            except (Error, OperationalError):
                self.connection.rollback()
                try:
                    cursor.execute(SQLv3)
                except (Error, OperationalError):
                    self.connection.rollback()
                    warnings.warn("Error retrieving citydb version")
                    return -1
                else:
                    (version,) = cursor.fetchone()
                    return version.split(",")[0][1:]
            else:
                version = cursor.fetchone()
                return version

    @property
    def srs(self) -> int:
        """
        Return the citydb srs.
        """

        SQL = """
                SELECT srid from citydb.database_srs LIMIT 1
              """

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(SQL)
            except (Error, OperationalError):
                self.connection.rollback()
                raise PostgreSQLInterfaceException("Error getting SRS from Database")
            else:
                srs = cursor.fetchone()
                return srs[0]

    @property
    def extent(self):
        """
        Return extent for QGIS
        """
        SQL = """
                SELECT
                    ST_Xmin(
                        ST_estimatedextent('citydb','cityobject','envelope')
                    ) as x_min,
                    ST_Ymin(
                        ST_estimatedextent('citydb','cityobject','envelope')
                    ) as y_min,
                    ST_Xmax(
                        ST_estimatedextent('citydb','cityobject','envelope')
                    ) as x_max,
                    ST_Ymax(
                        ST_estimatedextent('citydb','cityobject','envelope')
                    ) as y_max
              """

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(SQL)
            except (Error, OperationalError):
                self.connection.rollback()
                raise PostgreSQLInterfaceException(
                    "Error getting Exitmated extent from Database"
                )
            else:
                extent = cursor.fetchone()
                return extent

    def close_connection(self):
        """
        Close the active connection
        """

        try:
            self.connection.close()
        except InterfaceError:
            raise PostgreSQLInterfaceException("Error closing connection")
