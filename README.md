# Description

This plugin allows to load stored in a [3D CityDB](https://www.3dcitydb.org/3dcitydb/) in [QGIS](http://www.qgis.org). Is it possible to load the data in a 2D and 3D view.

**Important notice**: this plugin is currently in the development phase. Only **PostgreSQL** is supported and currently only **LOD2** data can be loaded. Pull Requests are welcome!

## Install from ZIP

The plugin can be installed using the _Install from ZIP_ Function in the Plugins Window (_Plugins_>_Installs und manage plugins_).

## How use the plugin

After enabling the plugin, there will be a new entry in the "Database" Menu. Selecting this option will load a new dockwidget.

## 3DCityDB Explorer Widget

- _Databases_: This is a list of the current PostgreSQL connection saved in QGIS.
- _Connect_: Create a connection with the selected Database.
- _Max Features_: The max number of features that will be loaded in QGIS. This is useful if requesting data for a big extent. This limit remains valid also when using zoom or pan function.
- _Add buildings_: Add the Buildings for the current extent.
- _Edit Attributes_: Start the edit modus. The mouse cursor wll change in a cross icon and with a click on building is is possible to edit its attributes. Clicking once again on this button will stop the edit modus.

## License

Copyright (C) 2021
Chair of Geoinformatics
Technical University of Munich, Germany
https://www.gis.bgu.tum.de/

This source is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option)
any later version.

This code is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

The 3D City Database is jointly developed with the following cooperation partners:

- virtualcitySYSTEMS GmbH, Berlin <http://www.virtualcitysystems.de/>
- M.O.S.S. Computer Grafik Systeme GmbH, Taufkirchen <http://www.moss.de/>
