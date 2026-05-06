#!/usr/bin/env python3
"""PyQt6 menu bar for GhostBot UI migration."""

from PyQt6.QtWidgets import QMenuBar, QMenu, QAction, QMessageBox
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtCore import Qt


class GhostBotMenu(QMenuBar):
    """Menu bar for GhostBot application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # File menu
        file_menu = self.addMenu("File")
        
        # Import character config
        import_action = QAction("Import character config", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self._import_char_config)
        file_menu.addAction(import_action)
        
        # Export character config
        export_action = QAction("Export character config", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._export_char_config)
        file_menu.addAction(export_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Shutdown server
        shutdown_action = QAction("Shutdown server", self)
        shutdown_action.triggered.connect(self._shutdown_server)
        file_menu.addAction(shutdown_action)
        
        # Auto-login configuration
        from GhostBot.UX.autologin.main import GhostBotAutoLogin
        auto_login_action = QAction("Auto-login configuration", self)
        auto_login_action.triggered.connect(
            lambda: GhostBotAutoLogin(parent, client=None)
        )
        file_menu.addAction(auto_login_action)
        
        # Separator
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(parent.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = self.addMenu("Help")
        
        # About action
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _import_char_config(self) -> None:
        """Import character configuration from file."""
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        files, _ = QFileDialog.getOpenFileNames(
            parent=self,
            caption="Import character config",
            directory=os.path.join(data_path, 'GhostBot'),
            filter="YAML files (*.yml);;All files (*)"
        )
        
        if files:
            for file in files:
                self.log_message(f"Importing character config from {file}")
    
    def _export_char_config(self) -> None:
        """Export character configuration to file."""
        from PyQt6.QtWidgets import QFileDialog
        import os
        
        data_path = os.environ.get('HOME', os.environ.get('LOCALAPPDATA'))
        file_path, _ = QFileDialog.getSaveFileName(
            parent=self,
            caption="Export character config",
            directory=os.path.join(data_path, 'GhostBot'),
            filter="YAML files (*.yml);;All files (*)",
            options=QFileDialog.Option.OverwriteQuery
        )
        
        if file_path:
            self.log_message(f"Exporting character config to {file_path}")
    
    def _shutdown_server(self) -> None:
        """Shutdown the bot server."""
        reply = QMessageBox.question(
            self,
            "Shutdown Server",
            "Are you sure you want to shutdown the bot server?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.parent().client.shutdown_server()
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About GhostBot",
            "<h3>GhostBot</h3>" +
            "<p>A bot for your game character.</p>" +
            "<p>Version 0.1.0</p>"
        )
    
    def log_message(self, message: str) -> None:
        """Log a message (placeholder for actual logging)."""
        pass
