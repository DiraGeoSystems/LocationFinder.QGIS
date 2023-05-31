#!/bin/bash
LRELEASE=$1
LOCALES=$2
PREFIX=location_finder

for LOCALE in ${LOCALES}
do
    echo "Processing: ${LOCALE}.ts"
    # Note we don't use pylupdate with qt .pro file approach
    # as it is flakey about what is made available.
    $LRELEASE "$PREFIX/i18n/$LOCALE.ts"
done
