@rem Publish the plugin to plugins.qgis.org:
@rem Step 1: create a zip archive
@rem Step 2: upload to plugins.qgis.org

@set ARCHIVE=location_finder.zip

@rem QGIS needs a LICENSE file in the plugin zip:
copy LICENSE .\location_finder

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
@rem Cleanup: delete the copied file:
@del /f /q .\location_finder\LICENSE
