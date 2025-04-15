#!/bin/sh
# Publish the plugin to plugins.qgis.org
# Step 1: create a zip archive
# Step 2: upload to plugins.qgis.org

ZIPTOOL=/usr/bin/zip
ARCHIVE=location_finder.zip

# QGIS needs a LICENSE file in the plugin zip:
cp LICENSE ./location_finder

test -f "$ARCHIVE" && rm -f "$ARCHIVE"
"$ZIPTOOL" -r "$ARCHIVE" ./location_finder && cat << EOF

Upload $ARCHIVE to https://plugins.qgis.org/plugins

 - either interactively on the web page,
 - or using the plugin_upload.py script

EOF

# Cleanup: delete the copied file:
rm -f location_finder/LICENSE
