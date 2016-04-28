# -*- coding: utf-8 -*-

from qgis.gui import QgsMapToolIdentify
from qgis.core import QGis
from PyQt4.QtGui import QCursor
from PyQt4.QtCore import Qt
import sys


class IdentifyFeature(QgsMapToolIdentify):
    def __init__(self, canvas):
        super(QgsMapToolIdentify, self).__init__(canvas)
        self.canvas = canvas

    def activate(self):
        self.canvas.setCursor(QCursor(Qt.CrossCursor))

    def canvasReleaseEvent(self, mouseEvent):
        x = mouseEvent.x()
        y = mouseEvent.y()
        id_feat = self.identify(x, y, self.ActiveLayer, self.VectorLayer)
        for feature in id_feat:
            geom = feature.mFeature.geometry()
            if geom.type() == QGis.Polygon:
                str_feature = "Feature ID: {} ".format(feature.mFeature.id())
                x = geom.asPolygon()
                numPts = 0
                for ring in x:
                    numPts += len(ring)
                #print("num points : {np}".format(np=numPts))
                if numPts == 5:
                    #QgsMessageLog.logMessage(str_feature, 'parametric_draw')
                    print(str_feature, ring, ring[3].sqrDist(ring[0]), self.is_rectangle(ring))

    def is_rectangle(self, arr_Points):
        a = arr_Points[3].sqrDist(arr_Points[0])
        b = arr_Points[1].sqrDist(arr_Points[0])
        h = arr_Points[3].sqrDist(arr_Points[1])
        c = arr_Points[1].sqrDist(arr_Points[2])
        d = arr_Points[3].sqrDist(arr_Points[2])
        print(a,b,h, abs(a + b - h), c,d, abs(c + d - h))
        # TODO apres le cafe retourner un QRECT ou None

        return (abs(a+b-h) < sys.float_info.min) and (abs(c + d - h) < sys.float_info.min)

