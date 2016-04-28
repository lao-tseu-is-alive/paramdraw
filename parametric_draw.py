# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Parametric_Draw
                                 A QGIS plugin
 allow to draw parametric objects
                              -------------------
        begin                : 2016-04-27
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Ville de Lausanne
        email                : cgil@lausanne.ch
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QLineEdit
from qgis.gui import QgsMapTool, QgsMapToolEmitPoint
from qgis.core import QgsMapLayer, QgsRectangle, QgsFeature
from qgis.core import QgsVectorDataProvider, QgsGeometry
# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from parametric_draw_dockwidget import Parametric_DrawDockWidget
from identify_feature import IdentifyFeature
# from point_tool import PointTool
import os.path


class Parametric_Draw:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Parametric_Draw_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Parametric Drawing')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'Parametric_Draw')
        self.toolbar.setObjectName(u'Parametric_Draw')

        # print "** INITIALIZING Parametric_Draw"

        self.pluginIsActive = False
        self.dockwidget = None

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
        return QCoreApplication.translate('Parametric_Draw', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            checkable_flag=False,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        action.setCheckable(checkable_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # TODO stocker les differentes actions dans des variables de la classe
        icon_path = ':/plugins/Parametric_Draw/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Parametric Drawing'),
            callback=self.run,
            parent=self.iface.mainWindow())
        self.add_action(
            icon_path,
            text=self.tr(u'Insert Point'),
            callback=self.get_point,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            checkable_flag=True)

        self.add_action(
            icon_path,
            text=self.tr(u'Select Shape '),
            callback=self.select_shape,
            parent=self.iface.mainWindow(),
            enabled_flag=False,
            checkable_flag=True)

        self.identify_tool = IdentifyFeature(self.iface.mapCanvas())
        self.identify_tool.deactivated.connect(self.select_shape_uncheck)
        self.pointEmitter = QgsMapToolEmitPoint(self.iface.mapCanvas())
        self.pointEmitter.canvasClicked.connect(self.retrieve_point_value)
        self.pointEmitter.deactivated.connect(self.point_emitter_uncheck)

    # --------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        # print "** CLOSING Parametric_Draw"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        # print "** UNLOAD Parametric_Draw"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Parametric Drawing'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            # print "** STARTING Parametric_Draw"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = Parametric_DrawDockWidget()

            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)
            self.actions[1].setEnabled(True)
            self.actions[2].setEnabled(True)
            self.dockwidget.show()

    def get_point(self):
        if self.dockwidget is None:
            self.run()
        self.iface.mapCanvas().setMapTool(self.pointEmitter)

    def retrieve_point_value(self, point, button):
        print("retrieve_point_value Clicked coords", " x: " + str(point.x()) +
              " Y: " + str(point.y()))
        self.dockwidget.x_edit.setText(str(point.x()))
        self.dockwidget.y_edit.setText(str(point.y()))

        try:
            width = float(self.dockwidget.width_edit.text())
            height = float(self.dockwidget.height_edit.text())
        except ValueError:
            QMessageBox.warning(None, "No!", "Insert float values")
            return

        layer = self.iface.activeLayer()
        if not layer or layer.type() != QgsMapLayer.VectorLayer:
            QMessageBox.warning(None, "No!", "Select a vector layer")
            return

        rect = QgsRectangle(point.x() - width / 2.0,
                            point.y() - height / 2.0,
                            point.x() + width / 2.0,
                            point.y() + height / 2.0)

        rect = self.iface.mapCanvas().mapRenderer().mapToLayerCoordinates(layer, rect)
        caps = layer.dataProvider().capabilities()

        print(rect.asWktPolygon())
        if caps & QgsVectorDataProvider.AddFeatures:
            feat = QgsFeature()
            # feat.addAttribute(0, 'hello')
            feat.setGeometry(QgsGeometry.fromWkt(rect.asWktPolygon()))
            (res, outFeats) = layer.dataProvider().addFeatures([feat])
            layer.triggerRepaint()
            # self.iface.mapCanvas().refresh()


    def point_emitter_uncheck(self):
        self.actions[1].setChecked(False)

    def select_shape(self):
        self.iface.mapCanvas().setMapTool(self.identify_tool)

    def select_shape_uncheck(self):
        self.actions[2].setChecked(False)

