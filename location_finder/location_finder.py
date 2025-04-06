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
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QDateTime, QTimer, QUrl
from qgis.PyQt.QtGui import QIcon, QColor
from qgis.PyQt.QtWidgets import QAction, QLabel, QFrame
from qgis.PyQt.QtNetwork import QNetworkRequest
from qgis.core import Qgis, QgsMessageLog, QgsProject
from qgis.core import QgsPointXY, QgsRectangle
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.core import QgsBlockingNetworkRequest
from qgis.gui import QgisInterface, QgsMapCanvas, QgsMapToolEmitPoint, QgsVertexMarker

# Initialize Qt resources from file resources.py
from .resources import *

from .location_finder_dockwidget import LocationFinderDockWidget
from .config_dialog import ConfigDialog
from .location import Location
from .config import Config
from .location_marker_item import LocationMarkerItem

import os.path
import requests
import json


# This plugin has one action, opening the LocationFinder dock window,
# and no toolbar (we simply add our only action to the Plugins toolbar).
# Thus we can greatly simplify Plugin Builder's boilerplate code.

class LocationFinderPlugin:
    """
    Implementation of the QGIS Plugin. Required methods are
    the constructor __init__(), initGui(), and unload().
    Provisions for localization are kept from the generated
    boilerplate code but not yet really used.
    """

    def __init__(self, iface: QgisInterface):
        """Plugin class constructor, will be passed a QgisInterface
        instance, which allows manipulation of the QGIS application"""

        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LocationFinder_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.pluginIsActive = False
        self.dockWidget = None
        self.configDialog = None
        self.openAction = None
        self.markers = {}

        self.config = Config()
        self.config.load()

        # Throttled auto-requesting:
        self.requestDelay = 300   # milliseconds # TODO configurable?
        self.scheduleTime = None  # time scheduled (ms since epoch)
        self.timer = QTimer()
        self.timer.setSingleShot(True)

        # Cached transformation:
        self.cachedTrafo = None
        self.trafoFromSrid = None
        self.trafoToSrid = None


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('LocationFinder', message)


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        if self.config.debugMode:
            logInfo("** initGui LocationFinder")

        icon = QIcon(':/plugins/location_finder/icon.png')
        text = self.tr(u'Open LocationFinder')
        parent = self.iface.mainWindow()
        openAction = QAction(icon, text, parent)
        openAction.triggered.connect(self.open)
        openAction.setEnabled(True)
        openAction.setObjectName("locationFinderAction")
        openAction.setStatusTip("Open LocationFinder dock window")  # shows on app's status bar
        openAction.setWhatsThis("Open LocationFinder dock window (whats this)") # TODO where/when does this show?

        self.openAction = openAction
        self.iface.addToolBarIcon(self.openAction)
        self.iface.addPluginToMenu(self.tr(u'&LocationFinder'), self.openAction)

        self.reverseTool = QgsMapToolEmitPoint(self.canvas)
        self.reverseTool.canvasClicked.connect(self.reverseClicked)
        self.reverseTool.setToolName("Reverse Geocode")
        reverseAction = QAction(icon, self.tr(u'Reverse Geocode'), parent)
        reverseAction.triggered.connect(self.reverse)
        reverseAction.setEnabled(True)
        reverseAction.setObjectName("reverseGeocodeAction")
        reverseAction.setStatusTip("Click on map to reverse geocode location")  # shows on status bar
        reverseAction.setWhatsThis("Click on map to reverse geocode location")  # TODO shown where/when?
        self.reverseAction = reverseAction
        self.iface.addToolBarIcon(self.reverseAction)
        self.iface.addPluginToMenu(self.tr(u'&LocationFinder'), self.reverseAction)


    def unload(self):
        """Cleanup when plugin is unloaded: remove menu items and icons"""
        if self.config.debugMode:
            logInfo("** unload LocationFinder")
        self.config.save()
        self.dropMarkers()
        self.iface.removePluginMenu(self.tr(u"&LocationFinder"), self.openAction)
        self.iface.removeToolBarIcon(self.openAction)
        self.iface.removePluginMenu(self.tr(u"&LocationFinder"), self.reverseAction)
        self.iface.removeToolBarIcon(self.reverseAction)


    def onConfigClicked(self):
        """User clicked the Config button on the dock widget: show the (modal) config dialog"""
        self.configDialog.setConfig(self.config)
        self.configDialog.show()
        result = self.configDialog.exec_()
        if result:  # user clicked OK
            self.configDialog.getConfig(self.config)
            self.config.save()
            self.dockWidget.lineEditService.setText(self.config.url)
            self.dockWidget.checkBoxAuto.setChecked(self.config.autoQuery)
            if self.config.url:
                self.doVersionRequest(self.config.url)
        #else: user canceled


    def onServiceEnter(self):
        self.clearResults()
        s = self.dockWidget.lineEditService.text()
        if len(s) > 0:
            self.doVersionRequest(s)


    def onQueryEnter(self):
        self.scheduleLookup(immediate=True)


    def onQueryEdited(self):
        # called when the user edited text (not when programmatically modified)
        self.config.autoQuery = self.dockWidget.checkBoxAuto.isChecked()
        if self.config.autoQuery:
            self.scheduleLookup(immediate=False)


    def onAutoQueryChanged(self):
        self.config.autoQuery = self.dockWidget.checkBoxAuto.isChecked()
        self.config.save()


    def onClosePlugin(self):
        """Cleanup when the plugin's dock widget is closed"""
        if self.config.debugMode:
            logInfo("** onClosePlugin LocationFinder")
        self.clearResults()
        self.dropMarkers()
        #self.dockWidget.closingPlugin.disconnect(self.onClosePlugin)
        #self.dockWidget = None
        self.pluginIsActive = False


    def open(self):
        """Start the plugin: create and open the dock widget"""
        if self.config.debugMode:
            logInfo(f"** open LocationFinder pluginIsActive={self.pluginIsActive}")

        if not self.pluginIsActive:
            self.pluginIsActive = True

            if self.configDialog is None:
                self.configDialog = ConfigDialog()

            if self.dockWidget is None:
                # Create the dockWidget (after translation) and keep reference
                self.dockWidget = LocationFinderDockWidget()
                self.dockWidget.pushButtonConfig.clicked.connect(self.onConfigClicked)
                self.dockWidget.lineEditQuery.textEdited.connect(self.onQueryEdited)
                self.dockWidget.lineEditQuery.returnPressed.connect(self.onQueryEnter)
                # TODO nice-to-have: Escape clears query (and results)
                self.dockWidget.lineEditService.returnPressed.connect(self.onServiceEnter)
                self.dockWidget.checkBoxAuto.stateChanged.connect(self.onAutoQueryChanged)

                # connect to provide cleanup on closing of dockWidget
                self.dockWidget.closingPlugin.connect(self.onClosePlugin)

            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockWidget)
            self.dockWidget.show()

        self.dockWidget.lineEditService.setText(self.config.url)
        self.dockWidget.lineEditQuery.setText("")
        self.dockWidget.checkBoxAuto.setChecked(self.config.autoQuery)
        self.clearResults()


    def reverse(self):
        """Make reverse geocoding the active map tool"""
        if self.config.debugMode:
            logInfo("Making reverse geocoding the active map tool")
        if not self.pluginIsActive:
            self.open()
        self.canvas.setMapTool(self.reverseTool)


    def reverseClicked(self, map_pt: QgsPointXY, button: Qt.MouseButton):
        """Called when the reverse geocode tool clicked on the canvas"""
        logInfo(f"reverse click: x={map_pt.x()} y={map_pt.y()} btn={button}")
        if not self.pluginIsActive:
            self.open()
        if not self.dockWidget.lineEditService.text().strip():
            self.reportError("Cannot reverse geocode: no LocationFinder service configured; please do so in the Config dialog")
            return
        self.doReverseRequest(map_pt)


    def now(self):
        return QDateTime.currentMSecsSinceEpoch()


    def reportError(self, msg, duration=-1):
        logError(msg)
        mbar = self.iface.messageBar()
        # pushMessage(title:str, text:str, showMore:str, level = Info, duration:int = -1)
        # severity levels: Qgis.Info, Qgis.Warning, Qgis.Critical, Qgis.Success
        mbar.pushMessage("LocationFinder", msg, level=Qgis.Warning, duration=duration)


    def getFinderUrl(self, baseUrl, suffix):
        assert baseUrl is not None
        assert len(baseUrl) > 0
        url = baseUrl.lower()
        if url[-1] == '/':
            url = url[0:-1]
        #if url[-7:] != "/finder":
        #    url += "/finder"
        if url.endswith("/finder/version") or url.endswith("/api/v1/version"):
            url = url[:-8]  # strip trailing "/version"
        return f"{url}/{suffix}"


    def doVersionRequest(self, baseUrl=None):
        try:
            baseUrl = baseUrl or self.dockWidget.lineEditService.text()
            url = self.getFinderUrl(baseUrl, "version")
            text = self.doFinderRequest(url)
            self.dockWidget.plainTextEdit.setPlainText(text)
            self.config.save()
            self.showVersionResults(json.loads(text))
            # TODO remember some LF info: version, sref, reverse yes/no
        except Exception as e:
            self.reportError(f"error doing version request: {e}")
            self.dockWidget.plainTextEdit.setPlainText(str(e))


    def doLookupRequest(self, baseUrl=None, queryText=None):
        try:
            # TODO configurable timeout (coordinate with type throttling)
            baseUrl = baseUrl or self.dockWidget.lineEditService.text()
            queryText = queryText or self.dockWidget.lineEditQuery.text()
            url = self.getFinderUrl(baseUrl, "lookup")
            params = {"query": queryText}
            if self.config.filter:
                params["filter"] = self.config.filter
            if self.config.limit is not None and self.config.limit >= 0:
                params["limit"] = self.config.limit
            if self.config.sref is not None:
                params["sref"] = self.config.sref
            text = self.doFinderRequest(url, params)
            self.dockWidget.plainTextEdit.setPlainText(text)
            self.showLookupResults(json.loads(text))
        except Exception as e:
            self.reportError(f"Error doing lookup request: {e}")
            self.dockWidget.plainTextEdit.setPlainText(str(e))
            self.clearResults()


    def doReverseRequest(self, map_pt: QgsPointXY, baseUrl=None):
        # expect map_pt in project's crs
        # transform to sref in config (if given) or LF's crs (if known) or don't transform (let LF do it)
        # then build the LF request and self.showReverseResults (à la showLookupResults)
        try:
            baseUrl = baseUrl or self.dockWidget.lineEditService.text()
            url = self.getFinderUrl(baseUrl, "reverse")
            crs = QgsProject.instance().crs().authid()  # e.g. "EPSG:4326"
            (name,code) = crs.split(':', 2)
            assert name == "EPSG", "Project CRS authority is not EPSG"
            pt = map_pt # TODO transform to LF's crs (if known)
            # location: {"x":X, "y":Y, "spatialReference":{"wkid":9999}}  (Esri style)
            params = {"location": f'{{"x":{pt.x()},"y":{pt.y()},"spatialReference":{{"wkid":{int(code)}}}}}'}
            logInfo(f"distance={self.config.distance}")
            if self.config.distance is not None and self.config.distance > 0:
                params["distance"] = self.config.distance
            if self.config.filter:
                params["filter"] = self.config.filter
            if self.config.limit is not None and self.config.limit > 0:
                params["limit"] = self.config.limit
            if self.config.sref is not None:
                params["sref"] = self.config.sref
            text = self.doFinderRequest(url, params)
            self.dockWidget.plainTextEdit.setPlainText(text)
            self.showLookupResults(json.loads(text)) # TODO consider variant showReverseResults()
        except Exception as e:
            self.reportError(f"Error doing reverse request: {e}")
            self.dockWidget.plainTextEdit.setPlainText(str(e))
            self.clearResults()


    def doFinderRequest(self, url, params=None):
        """
        Do an HTTP GET on the given url (without query string) and query params,
        return the text content of the response. Use the QGIS network access
        infrastructure (so QGIS proxy settings apply), unless configured to
        use the popular requests library (understands redirects).
        """
        if self.config.useRequests:
            r = requests.get(url, params=params, timeout=0.5)
            if self.config.debugMode:
                logInfo(f"{r.status_code} GET {r.url}")
            r.raise_for_status()  # raise if status indicates error
            return r.text  # could also return r.json()
            # Note that requests also offers r.json() and throws
            # requests.exceptions.RequestException on error

        # use requests to urlencode and append params as query string:
        req = requests.Request('GET', url, params=params)
        url = req.prepare().url
        # but now use QGIS networking infrastructure to GET the url:
        request = QgsBlockingNetworkRequest()
        if self.config.debugMode:
            logInfo(f"do QGIS blocking GET {url}")
        err = request.get(QNetworkRequest(QUrl(url)))
        if err != QgsBlockingNetworkRequest.ErrorCode.NoError:
          raise Exception(request.errorMessage() or f"request failed (code={err})")
        reply = request.reply()
        content = reply.content()
        if self.config.debugMode:
            logInfo(f"{len(content)} bytes from GET {url}")
        return bytes(content).decode('utf-8', errors='ignore')
        # Sadly, the QGIS stuff does not expose the HTTP status code,
        # nor can I set a custom timeout (the QGIS configured timeout
        # applies, which is typically far to high for our use case).
        # Moreover: how can I make it handle HTTP redirects?


    def parseLocation(self, j, sref=None):
        # j is a single element of the locs list of the json returned by LF:
        # {id:42, type:"poi", name:"Stadtpark", ...} where ... is cx,cy and/or xmin,ymin,xmax,ymax
        id, kind, name = j['id'], j['type'], j['name']
        l = Location(id, kind, name)
        if 'cx' in j and 'cy' in j:
            l.setCenter(j['cx'], j['cy'], sref)
        if 'xmin' in j and 'ymin' in j and 'xmax' in j and 'ymax' in j:
            l.setExtent(j['xmin'], j['ymin'], j['xmax'], j['ymax'], sref)
        return l


    def parseLookupResults(self, j):
        # j is the json returned by LF: {ok:true, info:"ok", sref:4326, count:123, locs:[...]}
        assert j['ok'] is True
        sref = j['sref'] if 'sref' in j else None
        locs = j['locs']
        return [self.parseLocation(l, sref) for l in locs]


    def showFinderError(self, msg):
        self.clearResults()
        grid = self.dockWidget.gridLayoutResults
        label = QLabel()
        label.setText(f"<b>Error</b> from LocationFinder:<br>{msg}")
        label.setWordWrap(True)
        grid.addWidget(label, 0, 0)
        self.reportError(f"Error from LocationFinder: {msg}", duration=5)


    def clearResults(self):
        grid = self.dockWidget.gridLayoutResults
        clear_layout(grid)
        self.hideMarkers()


    def showVersionResults(self, j):
        if not j['ok']:
            self.showFinderError(j['info'])
            return
        self.clearResults()
        grid = self.dockWidget.gridLayoutResults
        def addRow(label, name, bold=False):
            row = grid.rowCount()
            left = QLabel()
            left.setText(label)
            grid.addWidget(left, row, 0)
            value = j[name] if name in j else "n/a"
            right = QLabel()
            right.setWordWrap(True)
            right.setToolTip(name)
            if bold: right.setText(f"<b>{value}</b>")
            else: right.setText(f"{value}")
            grid.addWidget(right, row, 1)
        def addSeparator():
            row = grid.rowCount()
            left = QFrame()
            left.setFrameStyle(QFrame.HLine | QFrame.Plain)
            grid.addWidget(left, row, 0)
            right = QFrame()
            right.setFrameStyle(QFrame.HLine | QFrame.Plain)
            grid.addWidget(right, row, 1)
        addRow("Version", "version", True)
        addRow("Description", "serviceDescription")
        addRow("CRS", "sref", True)
        addSeparator()
        addRow("Location count", "locationCount")
        addRow("Location types<br>(normalized)", "locationTypes")
        addRow("Explicit fields", "explicitFields")
        addRow("Index name", "indexName")
        addRow("Last modified", "lastModified")
        addRow("Total bytes", "totalBytes")
        addRow("Start time", "startTime", True)
        addSeparator()
        addRow("#version requests", "versionRequests")
        addRow("#lookup requests", "lookupRequests")
        addRow("#reverse requests", "reverseRequests")
        addRow("#location requests", "locationRequests")
        self.dockWidget.scrollArea.ensureVisible(0,0)


    def showLookupResults(self, j):
        if not j['ok']:
            self.showFinderError(j['info'])
            return
        self.clearResults()
        grid = self.dockWidget.gridLayoutResults
        locations = self.parseLookupResults(j)
        labels = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, loc in enumerate(locations):
            label = QLabel()
            text = f'<b>{loc.name}</b><br>{loc.type}<br>'
            if loc.hasExtent:
                text += " <a href='zoom'>zoom</a>"
            if loc.hasExtent or loc.hasCenter:
                text += " <a href='pan'>pan</a>"
            if i < len(labels):
                pt = QgsPointXY(loc.cx, loc.cy)
                trafo = self.getTrafo(loc.sref)
                pt = trafo.transform(pt)
                self.addMarker(labels[i], pt)
                style = "color:#C80050;font-weight:bold;font-size:large"
                text += f" - <span style=\"{style}\">{labels[i]}</span>"
            label.setText(text)
            label.setWordWrap(True)
            #label.linkHovered.connect(lambda x: QgsMessageLog.logMessage("hovered"))
            clickAction = self.getClickClosure(loc)
            label.linkActivated.connect(clickAction)
            grid.addWidget(label, 2*i, 0)
            frame = QFrame()
            frame.setFrameShape(QFrame.HLine)
            frame.setLineWidth(1)
            grid.addWidget(frame, 2*i+1, 0)
        self.dockWidget.scrollArea.ensureVisible(0,0)


    def getClickClosure(self, loc):
        def panToLocation():
            mapCanvas:QgsMapCanvas = self.iface.mapCanvas()
            point = QgsPointXY(loc.cx, loc.cy)
            trafo = self.getTrafo(loc.sref)
            point = trafo.transform(point)
            QgsMessageLog.logMessage(f"Panning map to {loc.cx},{loc.cy} for {loc}", level=Qgis.Info)
            mapCanvas.setCenter(point)
            mapCanvas.refresh() # TODO required?
        def zoomToLocation():
            mapCanvas:QgsMapCanvas = self.iface.mapCanvas()
            rect = QgsRectangle(loc.xmin, loc.ymin, loc.xmax, loc.ymax)
            trafo = self.getTrafo(loc.sref)
            rect = trafo.transform(rect)
            QgsMessageLog.logMessage(f"Zooming map to {loc.xmin},{loc.ymin},{loc.xmax},{loc.ymax} for {loc}", level=Qgis.Info)
            mapCanvas.setExtent(rect)
            mapCanvas.refresh() # TODO required? empirically: yes
        return lambda link: zoomToLocation() if link == "zoom" else panToLocation()


    def getTrafo(self, srid):
        """Get a transformation from the given SRID to project's CRS"""
        project = QgsProject.instance()  # TODO can this ever be None?
        ctx = project.transformContext()  # so datum transformations are considered
        dstCrs = project.crs()  # with QGIS, the CRS seems to be a project property
        if (self.cachedTrafo is not None and
            self.trafoFromSrid == srid and self.trafoToSrid == dstCrs.authid()):
            return self.cachedTrafo  # re-use cached trafo
        srcCrs = getCRS(srid)
        assert srcCrs.isValid(), f"crs for {srid} is not valid"
        assert dstCrs.isValid(), "project crs is not valid (!)"
        if self.config.debugMode:
            logInfo(f"Creating transformation from {srid} to {dstCrs.authid()}")
        self.cachedTrafo = QgsCoordinateTransform(srcCrs, dstCrs, ctx)
        self.trafoFromSrid = srid
        self.trafoToSrid = dstCrs.authid()
        return self.cachedTrafo


    def scheduleLookup(self, immediate=False):
        if immediate:
            self.scheduleTime = None
            self.timer.stop()
            self.doLookupRequest()
        else:
            self.scheduleTime = self.now()
            self.timer.timeout.connect(self.checkPendingLookup)
            self.timer.start(self.requestDelay)


    def checkPendingLookup(self):
        if self.scheduleTime is None: return
        # If timer is interval (not single show), uncomment next line:
        #if self.now() < self.scheduleTime + self.requestDelay: return
        self.scheduleTime = None
        self.timer.stop()
        self.doLookupRequest()


    #--- markers ------------------------------------------------


    def addMarker(self, char, map_pt):
        m = self.markers.get(char)
        if m is None:
            m = self.createMarker(char)
            self.markers[char] = m  # cache
        #m.setCenter(map_pt)
        m.setPosition(map_pt)
        m.show()
        self.canvas.scene().addItem(m)
        return m


    def hideMarkers(self):
        """remove all markers, but keep the object (can add/show again)"""
        for m in self.markers.values():
            m.hide()
            self.canvas.scene().removeItem(m)


    def dropMarkers(self):
        """remove and forget all location markers (they have to be recreated)"""
        self.hideMarkers()
        self.markers.clear()


    def createMarker(self, character):
        #m = QgsVertexMarker(self.canvas)
        #m.setColor(QColor(200,0,80))
        #m.setIconSize(12)
        #m.setPenWidth(3)
        #m.setIconType(QgsVertexMarker.ICON_X)
        m = LocationMarkerItem(self.canvas)
        m.setChar(character)
        return m


#=== utils ======================================================


def logInfo(msg):
    QgsMessageLog.logMessage(msg, level=Qgis.Info)


def logError(msg):
    QgsMessageLog.logMessage(msg, level=Qgis.Critical)


def getCRS(key):
    # EPSG:<code>
    # PROJ:<proj>
    # WKT:<wkt>
    # POSTGIS:<srid>
    # INTERNAL:<srsid>
    # given no prefix, WKT is assumed!
    if type(key) is int:
        key = f"EPSG:{key}"
    if type(key) is str:
        try:
            code = int(key)
            key = f"EPSG:{code}"
        except:
            pass
    return QgsCoordinateReferenceSystem(key)


# Clearing a Qt layout seems to be non-trivial; see:
# https://stackoverflow.com/questions/4272196/qt-remove-all-widgets-from-layout
from qgis.PyQt.QtWidgets import QLayout
def clear_layout(layout: QLayout, deleteWidgets=True):
    while layout.count() > 0:
        child = layout.takeAt(0) # child is a QLayoutItem
        if not child: continue
        if child.widget() and deleteWidgets:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout(), deleteWidgets)
