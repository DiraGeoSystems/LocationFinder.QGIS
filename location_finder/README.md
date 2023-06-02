
# LocationFinder client for QGIS

## Purpose

This plugin adds a dock widget to QGIS that allows using
a LocationFinder instance for interactive geocoding:
search for place names and zoom or pan the map accordingly.

## Scope

This plugin is meant for organizations that use LocationFinder
for geocoding based on their own location data, such as address
points and/or arbitrary points of interests. For more information,
please see <https://dirageosystems.ch/lf.en.html>

If you are looking for geocoding against global address data,
try another plugin that uses data from OpenStreetMap or Google
or other sources with global coverage, search "geocoding" on
<https://plugins.qgis.org/> to find other plugins.

## Usage

Install and activate the plugin, then open the dock widget
(click the “LocationFinder” button). In the dock widget's
*Service* field, enter your LocationFinder's base URL,
then hit Enter to test the connection and to remember
this base URL in your QGIS profile.

If the connection to the LocationFinder service is working,
type queries in the *Lookup* field. Results are reported
below. If the *Auto* checkbox is checked, queries are
issued while typing (more precisely: a short delay after
your last keystroke); if *Auto* is unchecked, queries are
issued only when hitting Enter while in the Lookup field.

## Licensing

This plugin is copyright (c) 2023 by Dira GeoSystems and
released as open source under the terms of the MIT License,
<https://opensource.org/license/MIT/>. To create your own
derivatives, consider starting from the source code repository
at <https://github.com/dirageosystems/LocationFinder.QGIS>
