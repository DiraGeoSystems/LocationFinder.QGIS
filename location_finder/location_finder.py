# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LocationFinder (a QGIS plugin)

 QGIS client for LocationFinder (interactive geocoding),
 see https://dirageosystems.ch/lf.en.html

 Initial boilerplate code generated by Plugin Builder,
 see http://g-sherman.github.io/Qgis-Plugin-Builder/

        begin                : 2023-05-26
        git sha              : $Format:%H$
        copyright            : (c) 2023 by ujr for Dira GeoSystems
        email                : ujr@dirageosystems.ch
        license              : MIT License
 ***************************************************************************/
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QDateTime, QTimer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QLabel, QFrame
from qgis.core import Qgis, QgsMessageLog, QgsSettings, QgsProject
from qgis.core import QgsPointXY, QgsRectangle
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgisInterface, QgsMapCanvas

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
from .location_finder_dockwidget import LocationFinderDockWidget
from .location import Location
import os.path
import requests


# This plugin has one action, opening the LocationFinder dock window,
# and no toolbar (we simply add our only action to the Plugins toolbar).
# Thus we can greatly simplify Plugin Builder's boilerplate code.

class LocationFinderPlugin:
    """
    Implementation of the QGIS Plugin. Required methods are
    the constructor __init__(), initGui(), and unload().
    Provisions for localization are kept from the generated
    boilerplate code but yet really used.
    """

    def __init__(self, iface: QgisInterface):
        """Plugin class constructor, will be passed a QgisInterface
        instance, which allows manipulation of the QGIS application"""

        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'LocationFinder_{}.qm'.format(locale))

        QgsMessageLog.logMessage("Locale path: {}".format(locale_path), level=Qgis.Info) # TODO DEBUG DROP

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.pluginIsActive = False
        self.dockwidget = None
        self.action = None

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
        #QgsMessageLog.logMessage("** initGui LocationFinder", level=Qgis.Info)

        icon_path = ':/plugins/location_finder/icon.png'

        icon = QIcon(icon_path)
        text = self.tr(u'Open LocationFinder')
        parent = self.iface.mainWindow()
        action = QAction(icon, text, parent)
        action.triggered.connect(self.run)
        action.setEnabled(True)
        action.setObjectName("locationFinderAction")
        action.setStatusTip("Open LocationFinder dock window")  # shows on app's status bar
        action.setWhatsThis("Open LocationFinder dock window (whats this)") # TODO where/when does this show?

        self.action = action
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(self.tr(u'LocationFinder'), self.action)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        QgsMessageLog.logMessage("** unload LocationFinder", level=Qgis.Info) # TODO TEST DROP
        self.iface.removePluginMenu(self.tr(u"&LocationFinder"), self.action)
        self.iface.removeToolBarIcon(self.action)


    def onConfigClicked(self):
        """User clicked the Config button on the dock widget: show the (modal) config dialog"""
        QgsMessageLog.logMessage("LocationFinder Plugin Config not yet implemented", level=Qgis.Warning)
        self.iface.messageBar().pushMessage("Oops", "Config not yet implemented, enter base URL into Service field", level=Qgis.Warning, duration=3) # TODO TEST DROP


    def onServiceEnter(self):
        self.clearResults()
        s = self.dockwidget.lineEditService.text()
        if len(s) > 0:
            self.doVersionRequest(s)


    def onQueryEnter(self):
        self.scheduleLookup(immediate=True)


    def onQueryEdited(self):
        # called when the user edited text (not when programmatically modified)
        autoQuery = self.dockwidget.checkBoxAuto.isChecked()
        if autoQuery:
            self.scheduleLookup(immediate=False)


    def onAutoQueryChanged(self):
        autoQuery = self.dockwidget.checkBoxAuto.isChecked()
        settings = QgsSettings()
        settings.setValue("locationfinder/autoQuery", "on" if autoQuery else "off")


    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        # disconnects:
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        # remove this statement if dockwidget is to remain for reuse
        # if plugin is reopened; commented since it causes QGIS to
        # crash when closing the docked window:
        #self.dockwidget = None
        self.pluginIsActive = False


    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING LocationFinder"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = LocationFinderDockWidget()
                self.dockwidget.pushButtonConfig.clicked.connect(self.onConfigClicked)
                self.dockwidget.lineEditQuery.textEdited.connect(self.onQueryEdited)
                self.dockwidget.lineEditQuery.returnPressed.connect(self.onQueryEnter)
                # TODO nice-to-have: Escape clears query (and results)
                self.dockwidget.lineEditService.returnPressed.connect(self.onServiceEnter)
                self.dockwidget.checkBoxAuto.stateChanged.connect(self.onAutoQueryChanged)

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            settings = QgsSettings()
            serviceUrl = settings.value("locationfinder/serviceUrl", "")
            self.dockwidget.lineEditService.setText(serviceUrl)
            autoQuery = settings.value("locationfinder/autoQuery", False)
            if type(autoQuery) is not bool:
                autoQuery = str(autoQuery)
                autoQuery = autoQuery.lower() in ["true", "on", "1", "enabled"]
            self.dockwidget.checkBoxAuto.setChecked(autoQuery)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.dockwidget.show()


    def now(self):
        return QDateTime.currentMSecsSinceEpoch()


    def reportError(self, msg):
        mbar = self.iface.messageBar()
        mbar.pushMessage("LocationFinder", msg, level=Qgis.Critical)


    def getFinderUrl(self, baseUrl, suffix):
        assert baseUrl is not None
        assert len(baseUrl) > 0
        url = baseUrl.lower()
        if url[-1] == '/':
            url = url[0:-1]
        if url[-7:] != "/finder":
            url += "/finder"
        return f"{url}/{suffix}"


    def getLookupUrl(self, baseUrl):
        return self.getFinderUrl(baseUrl, "lookup")


    def getVersionUrl(self, baseUrl):
        return self.getFinderUrl(baseUrl, "version")


    def doVersionRequest(self, baseUrl=None):
        try:
            baseUrl = baseUrl or self.dockwidget.lineEditService.text()
            url = self.getVersionUrl(baseUrl)
            r = requests.get(url, timeout=0.5)
            level = Qgis.Info if r.status_code < 400 else Qgis.Critical
            QgsMessageLog.logMessage(f"{r.status_code} GET {r.url}", level=level)
            self.dockwidget.plainTextEdit.setPlainText(r.text)
            r.raise_for_status() # raise error if status code indicates error
            settings = QgsSettings()
            settings.setValue("locationfinder/serviceUrl", baseUrl)
            self.showVersionResults(r.json())
        except requests.exceptions.RequestException as e:
            self.reportError(f"request failed: {e}")
            self.dockwidget.plainTextEdit.setPlainText(str(e))


    def doLookupRequest(self, baseUrl=None, queryText=None):
        try:
            # TODO configurable timeout (coordinate with type throttling)
            # TODO configurable query parameters (sref, filter, limit)
            baseUrl = baseUrl or self.dockwidget.lineEditService.text()
            queryText = queryText or self.dockwidget.lineEditQuery.text()
            url = self.getLookupUrl(baseUrl)
            r = requests.get(url, params={"query": queryText}, timeout=0.5)
            level = Qgis.Info if r.status_code < 400 else Qgis.Critical
            QgsMessageLog.logMessage(f"{r.status_code} GET {r.url}", level=level)
            r.raise_for_status() # raise error if status code indicates error
            self.dockwidget.plainTextEdit.setPlainText(r.text)
            locs = self.parseLookupResults(r.json())
            self.showLookupResults(locs)
        except requests.exceptions.RequestException as e:
            self.reportError(f"request failed: {e}")
            self.dockwidget.plainTextEdit.setPlainText(str(e))
            self.clearResults()


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


    def clearResults(self):
        grid = self.dockwidget.gridLayoutResults
        clear_layout(grid)


    def showVersionResults(self, j):
        self.clearResults()
        grid = self.dockwidget.gridLayoutResults
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
        self.dockwidget.scrollArea.ensureVisible(0,0)


    def showLookupResults(self, locations):
        self.clearResults()
        grid = self.dockwidget.gridLayoutResults
        for i, loc in enumerate(locations):
            label = QLabel()
            text = f'<b>{loc.name}</b><br>{loc.type}<br>'
            if loc.hasExtent:
                text += " <a href='zoom'>zoom</a>"
            if loc.hasExtent or loc.hasCenter:
                text += " <a href='pan'>pan</a>"
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
        self.dockwidget.scrollArea.ensureVisible(0,0)


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
        QgsMessageLog.logMessage(f"Creating transformation from {srid} to {dstCrs.authid()}", level=Qgis.Info)
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


#=== utils ======================================================

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
