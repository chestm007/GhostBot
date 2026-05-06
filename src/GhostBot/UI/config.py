#!/usr/bin/env python3
"""PyQt6 configuration for GhostBot UI."""

from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QApplication


# Application name and version
APP_NAME = "GhostBot"
APP_VERSION = "0.1.0"

# Dark theme colors
DARK_THEME = {
    "background": QColor("#1a1a1a"),
    "foreground": QColor("#cccccc"),
    "selection": QColor("#4ec9b0"),
    "window": QColor("#2d2d2d"),
    "border": QColor("#404040"),
    "highlight": QColor("#7ee787"),
    "error": QColor("#f47b60"),
    "warning": QColor("#f4b400"),
    "info": QColor("#4ec9b0"),
    "debug": QColor("#7ee787"),
}

# Font settings
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 9
FONT_FAMILY_SMALL = "Consolas"
FONT_SIZE_SMALL = 8

# Window settings
WINDOW_MIN_WIDTH = 400
WINDOW_MIN_HEIGHT = 300

# Settings keys
SETTINGS_KEYS = {
    "window/geometry": "windowGeometry",
    "window/state": "windowState",
    "ui/theme": "uiTheme",
    "ui/font": "uiFont",
}


def init_app(app: QApplication) -> None:
    """Initialize the application with theme and settings."""
    
    # Set application metadata
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    # Set default font
    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))
    
    # Apply dark theme
    app.setStyleSheet("""
        QWidget {
            background-color: "" + DARK_THEME["background"].name() + ";
            color: "" + DARK_THEME["foreground"].name() + ";
            font: "" + FONT_FAMILY + " " + str(FONT_SIZE) + "px;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #404040;
            border-radius: 6px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #505050;
        }
        
        QScrollBar::add-line, QScrollBar::sub-line {
            height: 0px;
        }
        
        QScrollBar::add-scroller, QScrollBar::sub-scroller {
            width: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #2d2d2d;
            height: 12px;
            margin: 0px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #404040;
            border-radius: 6px;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #505050;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        
        QScrollBar::add-scroller:horizontal, QScrollBar::sub-scroller:horizontal {
            height: 0px;
        }
    """)
    
    # Set high DPI scaling
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Initialize settings
    settings = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope)
    settings.beginGroup(SETTINGS_KEYS["ui/theme"])
    theme = settings.value("current", "dark")
    settings.endGroup()
    
    print(f"{APP_NAME} v{APP_VERSION} initialized with {theme} theme")
