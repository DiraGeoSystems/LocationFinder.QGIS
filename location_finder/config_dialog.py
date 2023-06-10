# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Configuration dialog for the LocationFinder QGIS plugin
 ***************************************************************************/
"""

import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'config_dialog_base.ui'))


from .config import Config


class ConfigDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(ConfigDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)


    def setConfig(self, config: Config):
        assert type(config) is Config
        self.lineEditUrl.setText(config.url or "")
        self.lineEditFilter.setText(config.filter or "")
        self.lineEditSref.setText(config.sref or "")
        self.spinBoxLimit.setValue(-1 if config.limit is None else config.limit)
        self.checkBoxAutoQuery.setChecked(config.autoQuery or False)
        self.checkBoxDebugMode.setChecked(config.debugMode or False)


    def getConfig(self, config: Config):
        assert type(config) is Config
        config.url = self.lineEditUrl.text().strip()
        config.filter = canonical(self.lineEditFilter.text())
        config.sref = canonical(self.lineEditSref.text())
        config.limit = self.spinBoxLimit.value()
        config.autoQuery = self.checkBoxAutoQuery.isChecked()
        config.debugMode = self.checkBoxDebugMode.isChecked()


def canonical(text):
    if text is None: return None
    text = str(text).strip()
    return text if text else None
