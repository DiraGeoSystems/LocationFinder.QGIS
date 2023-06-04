#!/bin/sh
# Deploy the plugin locally: copy it into
# the QGIS default profile's plugins folder

NAME="location_finder"
PLUGINS="$HOME/.local/share/QGIS/QGIS3/profiles/default/python/plugins"

test -d "$PLUGINS/$NAME" && {
    echo "Deleting previous $PLUGINS/$NAME"
    rm -r "$PLUGINS/$NAME"
}

echo "Copying $NAME to $PLUGINS"
cp -r "./$NAME" "$PLUGINS"
