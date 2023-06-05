@rem Publish the plugin to plugins.qgis.org:
@rem Step 1: create a zip archive
@rem Step 2: upload to plugins.qgis.org

@set ARCHIVE=location_finder.zip

if exist "%ARCHIVE%" del "%ARCHIVE%"
zip -r "%ARCHIVE%" .\location_finder
if errorlevel 1 goto oops

@echo Upload %ARCHIVE% to https://plugins.qgis.org/plugins
@echo  - either interactively on the web page,
@echo  - or using the plugin_upload.py script

goto done

:oops
echo "Publication failed (see messages above)"

:done
