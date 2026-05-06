#!/usr/bin/env python3
"""PyQt6 frame implementations for GhostBot UI migration."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Any
from .frame_base import FrameBase


class Frame(FrameBase):
    """Base frame widget for GhostBot UI.
    
    Provides a scrollable content area with proper padding.
    """
    
    def __init__(self, title: str, data: Any, parent=None):
        super().__init__(title, data, parent)
        
        # Create scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        # Create scroll widget
        self._scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(self._scroll_widget)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Placeholder for child widgets
        self._placeholder = QFrame()
        self._placeholder.setObjectName("placeholder")
        self._placeholder.setStyleSheet("""
            QFrame#placeholder {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        scroll_layout.addWidget(self._placeholder)
        
        # Set up scroll area
        self._scroll_area.setWidget(self._scroll_widget)
        
        # Add to content
        self._add_widget(self._scroll_area)
    
    def _get_scroll_widget(self) -> QWidget:
        """Get the scroll widget for adding children."""
        return self._scroll_widget
    
    def _get_placeholder(self) -> QFrame:
        """Get the placeholder frame."""
        return self._placeholder
    
    def add_child(self, child: QWidget) -> None:
        """Add a child widget to the frame."""
        self._placeholder.deleteLater()
        scroll_layout = self._scroll_widget.layout()
        scroll_layout.addWidget(child)


class AttackFrame(Frame):
    """Attack frame for selecting character attacks."""
    
    def __init__(self, title: str, data: Any, parent=None):
        super().__init__(title, data, parent)
        
        # Create attack display
        self._attack_label = QLabel("No attack selected", self)
        self._attack_label.setObjectName("attackLabel")
        self._attack_label.setWordWrap(True)
        self._attack_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._attack_label.setStyleSheet("""
            QLabel#attackLabel {
                padding: 15px;
                font-size: 14px;
                color: #cccccc;
                background-color: #252525;
                border-radius: 4px;
            }
        """)
        
        # Add to frame
        self.add_child(self._attack_label)
    
    @property
    def attack_label(self) -> QLabel:
        return self._attack_label
    
    def set_attack(self, attack_name: str, attack_data: dict) -> None:
        """Set the selected attack."""
        if attack_name:
            text = f"**{attack_name}**\n\n"
            for key, value in attack_data.items():
                text += f"{key}: {value}\n"
            self._attack_label.setText(text)
            self._attack_label.setStyleSheet("""
                QLabel#attackLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #4ec9b0;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)
        else:
            self._attack_label.setText("No attack selected")
            self._attack_label.setStyleSheet("""
                QLabel#attackLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #cccccc;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)


class BuffFrame(Frame):
    """Buff frame for selecting character buffs."""
    
    def __init__(self, title: str, data: Any, parent=None):
        super().__init__(title, data, parent)
        
        # Create buff display
        self._buff_label = QLabel("No buff selected", self)
        self._buff_label.setObjectName("buffLabel")
        self._buff_label.setWordWrap(True)
        self._buff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._buff_label.setStyleSheet("""
            QLabel#buffLabel {
                padding: 15px;
                font-size: 14px;
                color: #cccccc;
                background-color: #252525;
                border-radius: 4px;
            }
        """)
        
        # Add to frame
        self.add_child(self._buff_label)
    
    @property
    def buff_label(self) -> QLabel:
        return self._buff_label
    
    def set_buff(self, buff_name: str, buff_data: dict) -> None:
        """Set the selected buff."""
        if buff_name:
            text = f"**{buff_name}**\n\n"
            for key, value in buff_data.items():
                text += f"{key}: {value}\n"
            self._buff_label.setText(text)
            self._buff_label.setStyleSheet("""
                QLabel#buffLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #7ee787;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)
        else:
            self._buff_label.setText("No buff selected")
            self._buff_label.setStyleSheet("""
                QLabel#buffLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #cccccc;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)


class FairyFrame(Frame):
    """Fairy frame for selecting fairy companions."""
    
    def __init__(self, title: str, data: Any, parent=None):
        super().__init__(title, data, parent)
        
        # Create fairy display
        self._fairy_label = QLabel("No fairy selected", self)
        self._fairy_label.setObjectName("fairyLabel")
        self._fairy_label.setWordWrap(True)
        self._fairy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._fairy_label.setStyleSheet("""
            QLabel#fairyLabel {
                padding: 15px;
                font-size: 14px;
                color: #cccccc;
                background-color: #252525;
                border-radius: 4px;
            }
        """)
        
        # Add to frame
        self.add_child(self._fairy_label)
    
    @property
    def fairy_label(self) -> QLabel:
        return self._fairy_label
    
    def set_fairy(self, fairy_name: str, fairy_data: dict) -> None:
        """Set the selected fairy."""
        if fairy_name:
            text = f"**{fairy_name}**\n\n"
            for key, value in fairy_data.items():
                text += f"{key}: {value}\n"
            self._fairy_label.setText(text)
            self._fairy_label.setStyleSheet("""
                QLabel#fairyLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #f47b60;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)
        else:
            self._fairy_label.setText("No fairy selected")
            self._fairy_label.setStyleSheet("""
                QLabel#fairyLabel {
                    padding: 15px;
                    font-size: 14px;
                    color: #cccccc;
                    background-color: #252525;
                    border-radius: 4px;
                }
            """)
