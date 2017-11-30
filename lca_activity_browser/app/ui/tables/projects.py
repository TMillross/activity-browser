# -*- coding: utf-8 -*-
# from __future__ import print_function, unicode_literals
# from eight import *

from PyQt5 import QtCore, QtGui, QtWidgets
from bw2data import projects


class ProjectListModel(QtCore.QAbstractListModel):
    def rowCount(self, *args):
        return len(projects)

    def data(self, index, *args):
        row = index.row()
        names = sorted([project.name for project in projects])
        return names[row]


class ProjectListWidget(QtWidgets.QComboBox):
    def __init__(self):
        super(ProjectListWidget, self).__init__()
        self._model = ProjectListModel()
        self.setModel(self._model)
        default_index = sorted([project.name for project in projects]).index("default")
        self.setCurrentIndex(default_index)