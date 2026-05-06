#!/usr/bin/env python3
"""PyQt6 pet frame for GhostBot UI migration."""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel
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
