# -*- coding: utf-8 -*-
from PyQt5 import QtGui, QtWidgets


bold_font = QtGui.QFont()
bold_font.setBold(True)
bold_font.setPointSize(12)

def horizontal_line():
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line


def header(label):
    label = QtWidgets.QLabel(label)
    label.setFont(bold_font)
    return label


# COLORS values are RGB

class TableStyle:
        # STYLESHEETS
        stylesheet_current_activity = """
        QTableWidget {
            border-radius: 5px;
            background-color: rgb(224, 224, 224);
            border:1px solid rgb(96, 96, 96);
            margin:0px;
            }
        """


class ActivitiesTab:
    style_sheet_read_only ="""
        QTabWidget::pane {
            border-top: 0px solid rgb(128,0,0); /*red line (read-only indicator) - removed due to request */
            /*border-bottom: 3px solid rgb(128,0,0);*/
        }        
    """
    style_sheet_editable = """
        QTabWidget::pane {
            border-top: 3px solid rgb(0,128,0);
            /* border-bottom: 3px solid rgb(0,128,0);*/
        }        
        """


class ActivitiesPanel:
    style_sheet = """
    """

class TableItemStyle:
    COLOR_CODE = {
        'default': (0, 0, 0),  # black
        'product': (0, 132, 130),
        'reference product': (0, 132, 130),
        'name': (0, 2, 140),
        'activity': (0, 72, 216),
        'amount': (0, 0, 0),
        # 'unit': (51, 153, 255),
        'unit': (0, 0, 0),
        'location': (72, 0, 140),
        'database': (96, 96, 96),
        'categories': (0, 0, 0),
        'key': (0, 0, 0),
    }

    def __init__(self):
        self.brushes = {}
        for key, values in self.COLOR_CODE.items():
            self.brushes.update({
                key: QtGui.QBrush(QtGui.QColor(*values))
            })


style_activity_panel = ActivitiesPanel
style_activity_tab = ActivitiesTab
style_table = TableStyle()
style_item = TableItemStyle()