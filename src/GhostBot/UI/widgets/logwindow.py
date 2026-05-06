#!/usr/bin/env python3
"""PyQt6 log window for GhostBot UI migration."""

from PyQt6.QtWidgets import QPlainTextEdit, QFrame, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class LogWindow(QPlainTextEdit):
    """A scrollable log window for displaying application logs.
    
    This replaces the tkinter Text widget with a modern QPlainTextEdit
    that supports:
    - Line wrapping
    - Auto-scrolling
    - Custom styling
    - Search functionality
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up the frame
        self._frame = QFrame(self)
        self._frame.setObjectName("logFrame")
        self._frame.setStyleSheet("""
            QFrame#logFrame {
                background-color: #1a1a1a;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QFrame#logFrame::indicator {
                width: 0px;
                height: 0px;
            }
        """)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Set up the text editor
        self._text = QPlainTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setFont(QFont("Consolas", 9))
        self._text.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1a1a1a;
                color: #cccccc;
                padding: 8px;
                border: none;
                selection-background-color: #4ec9b0;
            }
            QPlainTextEdit::滚轮条 {
                background-color: #303030;
            }
        """)
        
        # Enable auto-scroll
        self._text.verticalScrollBar().setSingleStep(10)
        
        # Add to frame
        self._frame.setLayout(layout)
        layout.addWidget(self._text)
    
    @property
    def text(self) -> QPlainTextEdit:
        """Get the text editor widget."""
        return self._text
    
    def append(self, text: str) -> None:
        """Append text to the log."""
        self._text.append(text)
        self._text.verticalScrollBar().setValue(
            self._text.verticalScrollBar().maximum()
        )
    
    def append_formatted(self, text: str, level: str = "INFO") -> None:
        """Append formatted log text."""
        if level == "ERROR":
            color = "#f47b60"
        elif level == "WARNING":
            color = "#f4b400"
        elif level == "DEBUG":
            color = "#4ec9b0"
        else:
            color = "#cccccc"
        
        formatted = f"[{level}] {text}"
        self._text.append(formatted)
        self._text.verticalScrollBar().setValue(
            self._text.verticalScrollBar().maximum()
        )
    
    def clear(self) -> None:
        """Clear the log window."""
        self._text.clear()
    
    def get_text(self) -> str:
        """Get the current log text."""
        return self._text.toPlainText()
