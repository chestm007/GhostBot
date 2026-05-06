#!/usr/bin/env python3
"""PyQt6 tabbed widget for GhostBot UI migration."""

from PyQt6.QtWidgets import QTabWidget, QTabBar, QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont
from typing import Any, Callable


class ReorderableTabWidget(QTabWidget):
    """Tab widget that supports reordering and custom tab icons.
    
    This replaces the tkinter tabbedwidget with a modern, flexible
    implementation that supports:
    - Drag-and-drop tab reordering
    - Custom tab icons
    - Tab close buttons
    - Custom tab bar styling
    """
    
    tab_closed = pyqtSignal(int)  # Emitted when a tab is closed
    tab_renamed = pyqtSignal(str, str)  # Emitted when a tab is renamed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up custom tab bar
        self._tab_bar = ReorderableTabBar(self)
        self.setTabBar(self._tab_bar)
        
        # Enable drag and drop
        self.setMovable(True)
        
        # Set up close tab on double-click
        self._tab_bar.doubleClicked.connect(self._on_tab_double_clicked)
        
        # Set default font
        self.setFont(QFont("Segoe UI", 9))
    
    def add_tab(self, widget: QWidget, text: str, icon: QIcon | None = None,
                closable: bool = True) -> int:
        """Add a new tab.
        
        Args:
            widget: The widget to display in the tab
            text: The tab text
            icon: Optional icon for the tab
            closable: Whether the tab can be closed (default: True)
        
        Returns:
            The index of the new tab
        """
        tab = self._tab_bar.addTab(widget, text, icon=icon, closable=closable)
        return tab
    
    def remove_tab(self, index: int) -> None:
        """Remove a tab by index.
        
        Args:
            index: The index of the tab to remove
        """
        self.removeTab(index)
        self.tab_closed.emit(index)
    
    def close_tab(self, index: int) -> bool:
        """Close a tab by index.
        
        Args:
            index: The index of the tab to close
        
        Returns:
            True if the tab was closed, False if it can't be closed
        """
        if self.tabBar().tabButton(index, QTabBar.TabCloseButtonRole.CloseButton).isVisible():
            self.removeTab(index)
            self.tab_closed.emit(index)
            return True
        return False
    
    def _on_tab_double_clicked(self, index: int) -> None:
        """Handle tab double-click (shows tab menu)."""
        pass


class ReorderableTabBar(QTabBar):
    """Custom tab bar with drag-and-drop support and close buttons.
    
    This extends Qt's QTabBar to add:
    - Close buttons on each tab
    - Drag-and-drop tab reordering
    - Custom styling
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set up close button
        self.setTabsClosable(True)
        self.setMovable(True)
        
        # Set up double-click
        self.doubleClicked.connect(self._on_double_clicked)
        
        # Set default style
        self.setStyleSheet("""
            QTabBar::tab {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px 4px 0 0;
                padding: 8px 15px;
                color: #cccccc;
                font-size: 9px;
                min-width: 60px;
            }
            
            QTabBar::tab:selected {
                background-color: #3d3d3d;
                border-color: #7ee787;
            }
            
            QTabBar::tab:hover {
                background-color: #404040;
            }
            
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
            
            QTabBar::close-button {
                image: none;
                subcontrol-origin: padding;
                subcontrol-position: center right;
                top: -1px;
                right: -1px;
                border-image: none;
                width: 15px;
                height: 15px;
            }
            
            QTabBar::close-button:hover {
                background-color: #b0b0b0;
            }
            
            QTabBar::close-button:pressed {
                background-color: #a0a0a0;
            }
        """)
    
    def _on_double_clicked(self, index: int) -> None:
        """Handle tab double-click."""
        # Show tab context menu
        menu = self._create_tab_menu(index)
        menu.exec(self.mapToGlobal(self.tabRect(index).center()))
    
    def _create_tab_menu(self, index: int) -> QWidget:
        """Create the tab context menu."""
        menu = QWidget()
        layout = QVBoxLayout(menu)
        
        # Add actions
        close_action = self._create_action("Close", self._close_tab, index)
        rename_action = self._create_action("Rename", self._rename_tab, index)
        
        layout.addWidget(close_action)
        layout.addWidget(rename_action)
        
        return menu
    
    def _create_action(self, text: str, callback: Callable, index: int) -> QWidget:
        """Create a clickable widget that acts as an action."""
        label = QLabel(text, self)
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.setFixedHeight(25)
        label.setFixedWidth(100)
        
        def on_click():
            callback(index)
        
        label.clicked.connect(on_click)
        return label
    
    def _close_tab(self, index: int) -> None:
        """Close a tab."""
        self.parent().close_tab(index)
    
    def _rename_tab(self, index: int) -> None:
        """Rename a tab."""
        pass
