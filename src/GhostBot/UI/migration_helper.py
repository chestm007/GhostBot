#!/usr/bin/env python3
"""Migration script from tkinter to PyQt6 for GhostBot UI."""

import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette


def create_main_window(title="GhostBot") -> QFrame:
    """Create the main application window."""
    app = QApplication(sys.argv)
    main_frame = QFrame()
    main_frame.setWindowFlags(Qt.Window)
    main_frame.setWindowTitle(title)
    main_frame.setGeometry(100, 100, 800, 600)
    main_frame.setStyleSheet("QWidget { background-color: #1a1a1a; color: #cccccc; }")
    main_layout = QVBoxLayout(main_frame)
    main_layout.setContentsMargins(0, 0, 0, 0)
    return main_frame


def create_char_list_view(parent) -> QListView:
    """Create a character selection list view."""
    list_view = QListView(parent)
    list_view.setFixedWidth(163)
    list_view.setFixedHeight(439)
    list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
    list_view.setMouseTracking(True)
    list_view.setAlternatingRowColors(True)
    list_view.setStyleSheet("QListView { background-color: #646464; color: #eaeaea; }")
    return list_view


def create_tabbed_widget(parent, enable_reorder=True) -> QTabWidget:
    """Create a tabbed widget for the main content area."""
    tab_widget = QTabWidget(parent)
    tab_widget.setFixedWidth(508)
    tab_widget.setFixedHeight(230)
    tab_widget.setMovable(enable_reorder)
    tab_widget.setStyleSheet("""
        QTabWidget::pane { background-color: #2d2d2d; border: 1px solid #404040; }
        QTabBar::tab { background-color: #2d2d2d; border: 1px solid #404040; padding: 8px 15px; color: #cccccc; font-size: 9px; }
        QTabBar::tab:selected { background-color: #3d3d3d; border-color: #7ee787; }
    """)
    return tab_widget


def create_log_window(parent) -> QPlainTextEdit:
    """Create a log window for displaying application logs."""
    log_widget = QPlainTextEdit(parent)
    log_widget.setReadOnly(True)
    log_widget.setFont(QFont("Consolas", 9))
    log_widget.setStyleSheet("QPlainTextEdit { background-color: #1a1a1a; color: #cccccc; padding: 8px; }")
    return log_widget


def create_attack_frame(parent) -> QFrame:
    """Create an attack selection frame."""
    frame = QFrame(parent)
    frame.setObjectName("attackFrame")
    frame.setFixedHeight(120)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    label = QLabel("No attack selected", frame)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
    layout.addWidget(label)
    return frame


def create_buff_frame(parent) -> QFrame:
    """Create a buff selection frame."""
    frame = QFrame(parent)
    frame.setObjectName("buffFrame")
    frame.setFixedHeight(120)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    label = QLabel("No buff selected", frame)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
    layout.addWidget(label)
    return frame


def create_fairy_frame(parent) -> QFrame:
    """Create a fairy selection frame."""
    frame = QFrame(parent)
    frame.setObjectName("fairyFrame")
    frame.setFixedHeight(120)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(10, 10, 10, 10)
    label = QLabel("No fairy selected", frame)
    label.setWordWrap(True)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet("QLabel { padding: 10px; font-size: 12px; color: #cccccc; background-color: #252525; border-radius: 4px; }")
    layout.addWidget(label)
    return frame
