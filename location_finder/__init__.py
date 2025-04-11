# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LocationFinder (a QGIS plugin)

 QGIS client for LocationFinder (interactive geocoding),
 see https://www.dirageosystems.ch/locationfinder.html

 Initial boilerplate code generated by Plugin Builder,
 see http://g-sherman.github.io/Qgis-Plugin-Builder/

        begin                : 2023-05-26
        git sha              : $Format:%H$
        copyright            : (c) 2023 by ujr for Dira GeoSystems
        email                : ujr@dirageosystems.ch
        license              : MIT License
 ***************************************************************************/

 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """
    Load the LocationFinderPlugin class from file location_finder_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .location_finder_plugin import LocationFinderPlugin
    return LocationFinderPlugin(iface)
