# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets

from .inventory import ActivitiesTable
from .inventory import BiosphereFlowsTable
from .table import ABTableWidget, ABTableItem
from ..icons import icons
from ...signals import signals


class ExchangeTable(ABTableWidget):
    """ All tables shown in the ActivityTab are instances of this class (inc. non-exchange types)
    Differing Views and Behaviours of tables are handled based on their tableType
    todo(?): possibly preferable to subclass for distinct table functionality, rather than conditionals in one class
    The tables include functionalities: drag-drop, context menus, in-line value editing
    The read-only/editable status of tables is handled in ActivityTab.set_exchange_tables_read_only()
    Instantiated with headers but without row-data
    Then set_queryset() called from ActivityTab with params
    set_queryset calls Sync() to fill and format table data items
    todo(?): the variables which are initiated as defaults then later populated in set_queryset() can be passed at init
       Therefore this class could be simplified by removing self.qs,upstream,database defaults etc.
    todo(?): column names determined by properties included in the activity and exchange?
        this would mean less hard-coding of column titles and behaviour. But rather dynamic generation
        and flexible editing based on assumptions about data types etc.
    """
    COLUMN_LABELS = {  # {exchangeTableName: headers}
        "products": ["Amount", "Unit", "Product", "Location", "Uncertainty"],
        # technosphere inputs & Downstream product-consuming activities included as "technosphere"
        # todo(?) should the table functionality for downstream activities really be identical to technosphere inputs?
        "technosphere": ["Amount", "Unit", "Product", "Activity", "Location", "Database", "Uncertainty", "Formula"],
        "biosphere": ["Amount", "Unit", "Flow Name", "Compartments", "Database", "Uncertainty"],
    }
    def __init__(self, parent, tableType):
        super(ExchangeTable, self).__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setSortingEnabled(True)

        self.tableType = tableType
        self.column_labels = self.COLUMN_LABELS[self.tableType]
        self.setColumnCount(len(self.column_labels))
        # default values, updated later in set_queryset()
        self.qs, self.upstream, self.database = None, False, None
        # ignore_changes set to True whilst sync() executes to prevent conflicts(?)
        self.ignore_changes = False
        self.setup_context_menu()
        self.connect_signals()
        self.setSizePolicy(QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Maximum)
        )

    def setup_context_menu(self):
        # todo: different table types require different context menu actions
        self.delete_exchange_action = QtWidgets.QAction(
            QtGui.QIcon(icons.delete), "Delete exchange(s)", None
        )
        self.addAction(self.delete_exchange_action)
        self.delete_exchange_action.triggered.connect(self.delete_exchanges)

    def connect_signals(self):
        # todo: different table types require different signals connected
        signals.database_changed.connect(self.filter_database_changed)
        self.cellChanged.connect(self.filter_amount_change)
        self.cellDoubleClicked.connect(self.filter_double_clicks)

    def delete_exchanges(self, event):
        signals.exchanges_deleted.emit(
            [x.exchange for x in self.selectedItems()]
        )

    def dragEnterEvent(self, event):
        acceptable = (
            ActivitiesTable,
            ExchangeTable,
            BiosphereFlowsTable,
        )
        if isinstance(event.source(), acceptable):
            event.accept()

    def dropEvent(self, event):
        items = event.source().selectedItems()
        if isinstance(items[0], ABTableItem):
            signals.exchanges_add.emit([x.key for x in items], self.qs._key)
        else:
            print(items)
            print(items.exchange)
            signals.exchanges_output_modified.emit(
                [x.exchange for x in items], self.qs._key
            )
        event.accept()

    def filter_database_changed(self, database):
        if self.database == database:
            self.sync()

    def filter_amount_change(self, row, col):
        try:
            item = self.item(row, col)
            if self.ignore_changes:
                return
            elif item.text() == item.previous:
                return
            else:
                value = float(item.text())
                item.previous = item.text()
                exchange = item.exchange
                signals.exchange_amount_modified.emit(exchange, value)
        except ValueError:
            print('You can only enter numbers here.')
            item.setText(item.previous)

    def filter_double_clicks(self, row, col):
        """ handles double-click events rather than clicks... rename? """
        item = self.item(row, col)
        # double clicks ignored for these table types and item flags (until an 'exchange edit' interface is written)
        if self.tableType == "products" or self.tableType == "biosphere" or (item.flags() & QtCore.Qt.ItemIsEditable):
            return

        if hasattr(item, "exchange"):
            # open the activity of the row which was double clicked in the table
            if self.upstream:
                key = item.exchange['output']
            else:
                key = item.exchange['input']
            signals.open_activity_tab.emit("activities", key)
            signals.add_activity_to_history.emit(key)

    def set_queryset(self, database, qs, limit=100, upstream=False):
        # todo(?): rename function: it calls sync() - which appears to do more than just setting the queryset
        # todo: use table paging rather than a hard arbitrary 'limit'. Could also increase load speed
        #  .upstream() exposes the exchanges which consume this activity.
        self.database, self.qs, self.upstream = database, qs, upstream
        self.sync(limit)

    @ABTableWidget.decorated_sync
    def sync(self, limit=100):
        """ populates an exchange table view with data about the exchanges, bios flows, and adjacent activities """
        self.ignore_changes = True
        self.setRowCount(min(len(self.qs), limit))
        self.setHorizontalHeaderLabels(self.column_labels)

        if self.upstream:
            # ideally these should not be set in the data syncing function
            # todo: refactor so that on initialisation, the 'upstream' state is known so state can be set there
            self.setDragEnabled(False)
            self.setAcceptDrops(False)

        # edit_flag is passed to table items which should be user-editable.
        # Default flag for cells is uneditable - which still allows cell-selection/highlight
        edit_flag = [QtCore.Qt.ItemIsEditable]

        # todo: add a setting which allows user to choose their preferred number formatting, for use in tables
        # e.g. a choice between all standard form: {0:.3e} and current choice: {:.3g}. Or more flexibility
        amount_format_string = "{:.3g}"
        for row, exc in enumerate(self.qs):
            # adj_act is not the open activity, but rather one of the activities connected adjacently via an exchange
            # When open activity is upstream of the two...
            # The adjacent activity we want to view is the output of the exchange which connects them. And vice versa
            adj_act = exc.output if self.upstream else exc.input
            if row == limit:

                break

            if self.tableType == "products":
                # headers: "Amount", "Unit", "Product", "Location", "Uncertainty"
                self.setItem(row, 0, ABTableItem(
                    amount_format_string.format(exc.get('amount')), exchange=exc, set_flags=edit_flag, color="amount"))

                self.setItem(row, 1, ABTableItem(
                    adj_act.get('unit', 'Unknown'), color="unit"))

                self.setItem(row, 2, ABTableItem(
                    # correct reference product name is stored in the exchange itself and not the activity
                    adj_act.get('reference product') or adj_act.get("name") if self.upstream else
                    exc.get('reference product') or exc.get("name"),
                    exchange=exc, color="reference product"))

                self.setItem(row, 3, ABTableItem(
                    # todo: remove? it makes no sense to show the (open) activity location...
                    # showing exc locations (as now) makes sense. But they rarely have one...
                    # I believe they usually implicitly inherit the location of the producing activity
                    str(exc.get('location', '')), color="location"))

                # todo: can both outputs and inputs of a process both have uncertainty data?
                self.setItem(row, 4, ABTableItem(
                    str(exc.get("uncertainty type", ""))))

            elif self.tableType == "technosphere":
                # headers: "Amount", "Unit", "Product", "Activity", "Location", "Database", "Uncertainty", "Formula"

                self.setItem(row, 0, ABTableItem(
                    amount_format_string.format(exc.get('amount')), exchange=exc, set_flags=edit_flag, color="amount"))

                self.setItem(row, 1, ABTableItem(
                    adj_act.get('unit', 'Unknown'), color="unit"))

                self.setItem(row, 2, ABTableItem(  # product
                    # if statement used to show different activities for products and downstream consumers tables
                    # reference product shown, and if absent, just the name of the activity or exchange...
                    # would this produce inconsistent/unclear behaviour for users?
                    adj_act.get('reference product') or adj_act.get("name") if self.upstream else
                    exc.get('reference product') or exc.get("name"),
                    exchange=exc, color="reference product"))

                self.setItem(row, 3, ABTableItem(  # name of adjacent activity (up or downstream depending on table)
                    adj_act.get('name'), exchange=exc, color="name"))

                self.setItem(row, 4, ABTableItem(
                    str(adj_act.get('location', '')), color="location"))

                self.setItem(row, 5, ABTableItem(
                    adj_act.get('database'), color="database"))

                self.setItem(row, 6, ABTableItem(
                    str(exc.get("uncertainty type", ""))))

                self.setItem(row, 7, ABTableItem(
                    exc.get('formula', '')))

            elif self.tableType == "biosphere":
                # headers: "Amount", "Unit", "Flow Name", "Compartments", "Database", "Uncertainty"
                self.setItem(row, 0, ABTableItem(
                    amount_format_string.format(exc.get('amount')), exchange=exc, set_flags=edit_flag, color="amount"))

                self.setItem(row, 1, ABTableItem(
                    adj_act.get('unit', 'Unknown'), color="unit"))

                self.setItem(row, 2, ABTableItem(
                    adj_act.get('name'), exchange=exc, color="name"))

                self.setItem(row, 3, ABTableItem(
                    " - ".join(adj_act.get('categories', [])), color="categories"))

                self.setItem(row, 4, ABTableItem(
                    adj_act.get('database'), color="database"))

                self.setItem(row, 5, ABTableItem(
                    str(exc.get("uncertainty type", ""))))

                # todo: investigate BW: can flows have both a Formula and an Amount? Or mutually exclusive?
                # what if they have both, and they contradict? Is this handled in BW - so AB doesn't need to worry?
                # is the amount calculated and persisted separately to the formula?
                # if not - optimal behaviour of this table is: show Formula instead of amount in 1st col when present?
                self.setItem(row, 6, ABTableItem(exc.get('formula', '')))
        self.ignore_changes = False
