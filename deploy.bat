@rem Deploy the plugin locally:
@rem copy to QGIS default profile's plugin folder

@set NAME=location_finder
@set PLUGINS=%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins

rmdir "%PLUGINS%\%NAME%" /s /q

xcopy ".\%NAME%" "%PLUGINS%\%NAME%" /i /s /q /y

@pause
