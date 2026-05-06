#!/usr/bin/env python3
"""PyQt6 regen frame for GhostBot UI migration."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


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
        label.setStyleSheet("""
            QLabel {
                padding: 10px;
                font-size: 12px;
                color: #cccccc;
                background-color: #252525;
                border-radius: 4px;
            }
        """)
        
        layout.addWidget(label)
