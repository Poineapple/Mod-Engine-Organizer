import sys
import json
import os
from PyQt6.QtCore import QDir, Qt
from PyQt6.QtGui import QFileSystemModel
from PyQt6.QtWidgets import QStyledItemDelegate, QComboBox, QApplication, QTreeView, QWidget, QVBoxLayout, QLabel


def itemIDs():
    if hasattr(sys, '_MEIPASS'):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath(".")

    dictPath = os.path.join(base_path, 'parts.json')

    # Load key-value pairs from the JSON file
    with open(dictPath, 'r') as file:
        IDs = json.load(file)
        print(IDs)
    return IDs


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, itemIDs, parent=None):
        super(ComboBoxDelegate, self).__init__(parent)
        self.itemIDs = itemIDs

    def createEditor(self, parent, option, index):
        original_filename = index.data(
            EditableFileSystemModel.OriginalFileNameRole)
        self.currentFilePath = index.model().filePath(index)
        if original_filename in self.itemIDs:
            comboBox = QComboBox(parent)
            comboBox.addItem(original_filename)
            matchingIDs = [(id, self.itemIDs[id])
                           for id in self.itemIDs.keys() if id[:2] == original_filename[:2]]
            matchingIDs.sort(key=lambda x: x[1])
            for id, description in matchingIDs:
                comboBox.addItem(description, id)
            comboBox.currentIndexChanged.connect(self.renameFile)
            return comboBox
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QComboBox):
            currentText = index.data()
            editor.setCurrentText(currentText)
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText())
        else:
            super().setModelData(editor, model, index)

    def renameFile(self, index):
        comboBox = self.sender()
        # Retrieve the file name (key) from the data
        newFileName = comboBox.currentData()
        newFilePath = os.path.join(os.path.dirname(
            self.currentFilePath), newFileName)
        try:
            os.rename(self.currentFilePath, newFilePath)
            self.currentFilePath = newFilePath
        except Exception as e:
            print(f"Error renaming file: {e}")


class EditableFileSystemModel(QFileSystemModel):
    OriginalFileNameRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, itemIDs, parent=None):
        super().__init__(parent)
        self.itemIDs = itemIDs

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            file_path = self.filePath(index)
            file_name = os.path.basename(file_path)
            if file_name in self.itemIDs:
                return self.itemIDs[file_name]
        elif role == self.OriginalFileNameRole:
            file_path = self.filePath(index)
            file_name = os.path.basename(file_path)
            return file_name
        return super().data(index, role)

    def flags(self, index):
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable


class DirTreeView(QWidget):
    def __init__(self, path, itemIDs={}):
        super().__init__()
        self.path = path
        # Create a file system model
        self.model = EditableFileSystemModel(itemIDs)
        # Only display directories in the tree view by default
        self.model.setFilter(QDir.Filter.AllEntries |
                             QDir.Filter.NoDotAndDotDot)
        # Create a tree view widget
        self.tree_view = QTreeView()
        self.path_label = QLabel(f"Selected Mod: {path.split(os.sep)[-1]}")
        layout = QVBoxLayout()
        layout.addWidget(self.path_label)
        layout.addWidget(self.tree_view)
        self.setLayout(layout)

        self.model.setRootPath(path)
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(path))
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.tree_view.header().resizeSection(0, 450)
        self.tree_view.expandAll()
        delegate = ComboBoxDelegate(itemIDs)
        self.tree_view.setItemDelegateForColumn(0, delegate)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    IDs = itemIDs()
    # Create the directory tree view widget
    tree_view = DirTreeView(
        path="D:\\Games\\elden rang mods\\ModEngine-2.1.0.0-win64\\mod",
        itemIDs=IDs)
    tree_view.show()

    sys.exit(app.exec())
