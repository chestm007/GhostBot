#!/usr/bin/env python3
"""PyQt6 UI components for GhostBot migration."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt


class PetFrame(QFrame):
    """Pet frame for selecting pet companions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("petFrame")
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel("No pet selected", self)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
        layout.addWidget(label)


class RegenFrame(QFrame):
    """Regen frame for selecting regeneration options."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("regenFrame")
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel("No regen selected", self)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
        layout.addWidget(label)


class SellFrame(QFrame):
    """Sell frame for selling items."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sellFrame")
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel("No item selected for sell", self)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
        layout.addWidget(label)


class DeleteFrame(QFrame):
    """Delete frame for deleting characters."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("deleteFrame")
        self.setFixedHeight(120)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        label = QLabel("No character selected for deletion", self)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
        layout.addWidget(label)
