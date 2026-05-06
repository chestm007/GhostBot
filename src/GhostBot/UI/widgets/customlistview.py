#!/usr/bin/env python3
"""PyQt6 list view for character selection in GhostBot."""

from typing import Any
from PyQt6.QtWidgets import QListView, QAbstractItemView, QAbstractListModel, QListWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, QAbstractTableModel, QMimeData, QStringListModel, QModelIndex


class CharacterListModel(QAbstractListModel):
    """Model for character names in the list view."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._data = {}

    def set_characters(self, chars, data=None):
        """Set the list of characters."""
        self.beginResetModel()
        self._items = chars
        self._data = data or {}
        self.endResetModel()

    def rowCount(self, parent=Qt.NoParent):
        """Return number of characters."""
        return len(self._items)

    def data(self, index, role=0):
        """Return data for the given index."""
        if not index.isValid():
            return None
        name = self._items[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return name
        elif role == Qt.ItemDataRole.EditRole:
            return name
        elif role == Qt.ItemDataRole.UserRole:
            return self._data.get(name, {})
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Set data for the given index."""
        if not index.isValid():
            return False
        name = self._items[index.row()]
        if role == Qt.ItemDataRole.EditRole:
            self._items[index.row()] = value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
            return True
        return False

    def remove_item(self, index):
        """Remove an item by index."""
        if not index.isValid():
            return False
        row = index.row()
        if row < 0 or row >= len(self._items):
            return False
        name = self._items.pop(row)
        self._data.pop(name, None)
        self.beginRemoveRows(parent, row, row)
        self.endRemoveRows()
        self.dataChanged.emit(
            self.index(row, 0), self.index(row, 0),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
        )
        return True

    def insert_item(self, index, item):
        """Insert an item at the given row."""
        if index < 0 or index > len(self._items):
            return False
        self.beginInsertRows(parent, index, index)
        self._items.insert(index, item)
        self.endInsertRows()
        self.dataChanged.emit(
            self.index(index, 0), self.index(index, 0),
            [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]
        )
        return True

    def clear(self):
        """Clear all characters."""
        self.beginResetModel()
        self._items.clear()
        self._data.clear()
        self.endResetModel()
