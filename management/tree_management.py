from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView

from management.fw_container_items import ContainerItem, FileItem, GroupItem


class TreeManagement:
    def __init__(self, main_window):
        self.main_window = main_window
        self.ui = main_window.ui
        self.cache_files = {}
        tree = self.ui.treeView
        tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        tree.clicked.connect(self.tree_clicked)
        tree.expanded.connect(self.on_expanded)

        tree.setContextMenuPolicy(Qt.CustomContextMenu)
        tree.customContextMenuRequested.connect(self.open_menu)
        self.source_model = QtGui.QStandardItemModel()
        tree.setModel(self.source_model)

        self.populateTree()

    def tree_clicked(self, index):
        item = self.get_id(index)
        if isinstance(item, ContainerItem):
            self.ui.btn_new_analysis.setEnabled(item.has_analyses)
            self.current_item = item
        else:
            self.ui.btn_new_analysis.setEnabled(False)

    def populateTree(self):
        groups = self.main_window.fw_client.groups()
        for group in groups:
            group_item = GroupItem(self.source_model, group)

    def get_id(self, index):
        item = self.source_model.itemFromIndex(index)
        id = item.data()
        self.ui.txtID.setText(id)
        return item

    def open_menu(self, position):
        indexes = self.ui.treeView.selectedIndexes()
        if len(indexes) > 0:
            hasFile = False
            for index in indexes:
                item = self.source_model.itemFromIndex(index)
                if isinstance(item, FileItem):
                    hasFile = True

            menu = QtWidgets.QMenu()
            if hasFile:
                action = menu.addAction("Cache Selected Files")
                action.triggered.connect(self._cache_selected)
            menu.exec_(self.ui.treeView.viewport().mapToGlobal(position))

    def _cache_selected(self):
        indexes = self.ui.treeView.selectedIndexes()
        if len(indexes) > 0:
            for index in indexes:
                item = self.source_model.itemFromIndex(index)
                if isinstance(item, FileItem):
                    item._add_to_cache()

    def on_expanded(self, index):
        item = self.source_model.itemFromIndex(index)
        if hasattr(item, "_on_expand"):
            item._on_expand()

    def cache_selected_for_open(self):
        tree = self.ui.treeView
        self.cache_files = {}
        for index in tree.selectedIndexes():
            file_path = self.main_window.CacheDir
            item = self.source_model.itemFromIndex(index)
            if isinstance(item, FileItem):
                file_path = item._add_to_cache()

                # TODO: Handle only NIfTIs for now.
                # if ".zip" in str(file_path):
                #     input_zip = ZipFile(file_path, "r")
                #     zip_folder = Path(str(file_path).replace(".zip", ""))
                #     if not zip_folder.exists():
                #         os.makedirs(zip_folder)
                #     input_zip.extractall(zip_folder)

                self.cache_files[item.container.id] = str(file_path)
