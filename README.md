
# LocationFinder for QGIS

This repository contains a Plugin for QGIS that allows
using a LocationFinder instance for interactive geocoding.

Geocoding finds coordinates given a name (or an address).
Reverse geocoding finds the closest named point (or address)
given a point's coordinates.

The published version is online in the QGIS plugins repo
at <https://plugins.qgis.org/plugins/location_finder/>

This documentation addresses developers. For user-directed
documentation, see the [README.md](location_finder/README.md)
inside the plugin folder.

## Deploy locally (for testing)

Copy the [location_finder](./location_finder/) folder (not only
its contents) to your QGIS profile's python plugins folder:
`%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins` (Windows) or
`~/.local/share/QGIS/QGIS3/profiles/default/python/plugins` (Linux).

You may use the provided scripts [deploy.bat](./deploy.bat) or
[deploy.sh](./deploy.sh) for this purpose, and you may use the
[Plugin Reloader](https://plugins.qgis.org/plugins/plugin_reloader/)
plugin to reload the deployed plugin into a running instance of QGIS.

## Publish to plugins.qgis.org

Create a zip archive from the [location_finder](./location_finder/)
**folder** (not only the folder's contents) and upload it to
<https://plugins.qgis.org> (you will need an OSGeo ID). The
provided script [publish.sh](./publish.sh) may be helpful; for
detailed instructions, see <https://plugins.qgis.org/publish/>

## Technical Notes

- this is a Python Plugin for QGIS
- initial template created with the QGIS Plugin Builder,
  see <http://g-sherman.github.io/Qgis-Plugin-Builder/>
- the plugin itself consists of the [location_finder](./location_finder/)
  folder; a zip archive of it can be uploaded to the QGIS plugin repo
- I prefer keeping the plugin folder clear of dev and build tooling
  and thus moved things like Makefile, scripts/, and test/ out of it
  (the Makefile is therefore no longer valid and should be revised)
- UI created using the free Qt Designer that comes with the QGIS
  OSGeo4W installer (Windows .msi)
- tooling: VS Code with the Python extension (had to create *.env* file
  that sets the PYTHONPATH variable for QGIS and Qt stuff to be found)
- use pyrcc5 to compile *resources.qrc* into *resources.py* – pyrcc5
  comes with OSGeoW but requires *o4w_env.bat* to be run first (search
  the QGIS installation directory for this script) or pyrcc5 or one of
  its requirements will not be found
- warning: I'm new to QGIS development and I'm also new to Qt development
- message levels for use in `iface.messageBar().pushMessage()` and
  `QgsMessageLog.logMessage()` are: `Qgis.Info`, `Qgis.Warning`,
  `Qgis.Critical`, `Qgis.Success`

## Developer Resources

The *PyQGIS Developer Cookbook* at  
<http://www.qgis.org/pyqgis-cookbook/index.html>

The minimal QGIS Python plugin can be seen at  
<https://github.com/wonder-sk/qgis-minimal-plugin/>

The *Qt Designer Manual* at  
<https://doc.qt.io/qt-6/qtdesigner-manual.html>

About Python environments with VS Code see  
<https://code.visualstudio.com/docs/python/environments>

Documentation for the *requests* HTTP library at  
<https://requests.readthedocs.io/>
