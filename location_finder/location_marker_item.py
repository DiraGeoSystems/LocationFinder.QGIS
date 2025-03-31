# Custom map canvas item to show locations: a letter in a circle.
# Usage:
#   canvas = iface.mapCanvas()
#   m = LocationMarkerItem(canvas)
#   m.setPosition(QgsPointXY(123.4, 567.8)) # map coordinates
#   m.setChar('A');  m.setSize(20)
#   m.setColor(QColor(192, 192, 0, 127))  # translucent magenta
#   m.hide();  m.show();  canvas.scene().removeItem(m)
#
# The easiest way to draw a point marker on the map is to use the
# out-of-the-box QgsVertexMarker class; its setCenter(pt) expects
# a QgsPointXY in map coordinates.
#
# About custom map canvas items, see:
# https://docs.qgis.org/3.40/en/docs/pyqgis_developer_cookbook/canvas.html
#
# Examples of custom map canvas items (search "QgsMapCanvasItem" on GitHub):
# https://github.com/mitre/QgisTDC/blob/main/timeplayer/CanvasTextLayer.py
# https://github.com/PacktPublishing/Introduction-to-QGIS-Python-Programming/blob/master/Section%201/Video%201.5/custom_map_canvas_item.py
#
# To make the item keep its position on the map (not on the canvas):
# override updatePosition() and then convert remembered map coords
# to canvas coords. Consider calling setPos() from the Qt base class
# to set the local origin to simplify boundingRect() and paint().
# Note the types of the coordinate conversion methods:
# - toMapCoordinates(QPoint): QgsPointXY
# - toCanvasCoordinates(QgsPointXY): QPointF
# Also note that QRect and QRectF are x,y,w,h (not x0,y0,x1,y1).


from qgis.PyQt.QtGui import QColor, QPen, QFont, QPainter
from qgis.PyQt.QtCore import Qt, QPoint, QPointF, QRectF

from qgis.core import QgsPointXY
from qgis.gui import QgsMapCanvasItem


class LocationMarkerItem(QgsMapCanvasItem):

    def __init__(self, canvas):
        #super().__init__(canvas)
        QgsMapCanvasItem.__init__(self, canvas)
        self.size = 20
        self.char = "X"
        self.color = QColor(200,0,80,200) # slightly transparent (255=opaque) dark red
        self.position = QgsPointXY(0, 0)
        self.pen = None
        self.font = None
        self.updateGraphics()

    def setChar(self, char:str):
        self.char = char

    def char(self):
        return self.char

    def setSize(self, size:float):
        self.size = size
        self.updateGraphics()

    def setColor(self, color:QColor):
        self.color = color
        self.updateGraphics()

    def setPosition(self, map_pt:QgsPointXY):
        self.position = map_pt
        center = self.toCanvasCoordinates(self.position)
        self.setPos(center)

    def updatePosition(self):
        """called when map position/extent changed"""
        self.setPos(self.toCanvasCoordinates(self.position))
        #self.update()  # schedules a redraw -- required?

    def updateGraphics(self):
        """call this when size/color/etc changed"""
        self.pen = QPen(self.color, self.size/6, Qt.SolidLine)
        # Qt font weight is 0..99, 50=Normal, 63=DemiBold, 75=Bold
        self.font = QFont("Helvetica", int(self.size*.55), weight=69)

    def boundingRect(self):
        return QRectF(-self.size/2, -self.size/2, self.size, self.size)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)
        painter.setPen(self.pen)
        origin = QPoint(0, 0)
        painter.drawEllipse(origin, self.size/2, self.size/2)
        painter.setFont(self.font)
        metrics = painter.fontMetrics()
        h = metrics.height()
        w = metrics.width(self.char)
        pt = QPointF(-w/2, h/3.2)
        painter.drawText(pt, self.char)


# Call logInfo("foo") for "printf debugging":
from qgis.core import Qgis, QgsMessageLog
def logInfo(msg):
    QgsMessageLog.logMessage(msg, level=Qgis.Info)
