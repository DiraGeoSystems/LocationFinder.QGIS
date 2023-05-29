
# LocationFinder for QGIS

This repository contains a Plugin for QGIS that allows
using a LocationFinder instance for interactive geocoding.

Geocoding finds coordinates given a name (or an address).
Reverse geocoding finds the closest named point (or address)
given a point's coordinates.

**Installation:** copy the [location_finder](./location_finder/)
folder (not only its contents) to your QGIS profile's python plugin
folder: %APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/ (Windows)
or ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins (Linux)

## Technical Notes

- a Python Plugin for QGIS
- initial template created with the QGIS Plugin Builder,
  see [Plugin Builder Results](./location_finder/README.txt)
- UI created using the free Qt Designer that comes with the QGIS
  OSGeo4W installer (Windows .msi)
- the plugin itself consists of the [location_finder](./location_finder/)
  folder
- use pyrcc5 to compile *resources.qrc* into *resources.py* – pyrcc5
  comes with OSGeoW but requires *o4w_env.bat* to be run first (search
  the QGIS installation directory for this script) or pyrcc5 or one of
  its requirements will not be found
- warning: I'm new to QGIS development and I'm also new to Qt development

## Developer Resources

The *PyQGIS Developer Cookbook* at
<http://www.qgis.org/pyqgis-cookbook/index.html>

The *Qt Designer Manual* at
<https://doc.qt.io/qt-6/qtdesigner-manual.html>
