
# LocationFinder client for QGIS

## Purpose

This plugin adds a dock widget to QGIS that allows using
a LocationFinder instance for interactive geocoding:
search for place names and zoom or pan the map accordingly.

## Scope

This plugin is meant for organizations that use LocationFinder
for geocoding based on their own location data, such as address
points and/or arbitrary points of interests. For more information,
please see <https://dirageosystems.ch/#locationfinder>

If you are looking for geocoding against global address data,
try another plugin that uses data from OpenStreetMap or Google
or other sources with global coverage, search "geocoding" on
<https://plugins.qgis.org/> to find other plugins.

## Usage

Install and activate the plugin. Choose **Open LocationFinder**
from the Plugins menu (or click the button on the toolbar) to
open the *LocationFinder* dock widget. Click the “Config” button
to open the configuration dialog. As “Service URL” enter your
LocationFinder's base URL, something like `http://host:port/finder`
(before version 2) or `http://host:port/api/v1` (since version 2).
Click “OK” to close the dialog and remember this base URL in your
QGIS profile. (The service may also use https and there may be
a path component before the trailing /finder or /api/v1.)

The dock widget's *Service* field shows again the base URL.
The field is read-only, but if you hit Enter while in the
field, information about the LocationFinder service will be
retrieved and shown in the dock widget (connection test).

If the connection to the LocationFinder service is working,
type queries in the *Lookup* field. Results are reported
below. If the *Auto* checkbox is checked, queries are
issued while typing (more precisely: a short delay after
your last keystroke); if *Auto* is unchecked, queries are
issued only when hitting Enter while in the Lookup field.

The **Reverse Geocode** asks the configured LocationFinder
service for the nearest few locations to the click point.
The configuration options “max results” and “max distance”
determine how many locations to find at most, and at what
maximum distance from the click point (the server may impose
smaller limits). Note that a LocationFinder only supports
reverse geocoding if it has been prepared to do so.

## Licensing

This plugin is copyright (c) 2025 by Dira GeoSystems and
released as open source under the terms of the MIT License,
<https://opensource.org/license/MIT/>. To create your own
derivatives, consider starting from the source code repository
at <https://github.com/dirageosystems/LocationFinder.QGIS>

## Changelog

**next** show marker on map for (first few) result locations
• new tool for reverse geocoding (click on map to see nearest
locations, if supported by the configured service) • allow the
new LocationFinder 2.x URLs (ending in */api/v1/foo* instead
of */Finder/Foo*, but the latter is still supported) • use
`QgsNetworkAccessManager` (applies proxy settings) by default,
with a config option to use the popular `requests` module
(follows HTTP redirects) instead

**0.1.1** config dialog, various small improvements, remove
experimental flag

**0.1.0** first public release, marked experimental
