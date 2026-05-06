#!/usr/bin/env python3
"""PyQt6 frame base classes for GhostBot UI migration."""

from typing import Any, Protocol, runtime_checkable, Generic, TypeVar
from dataclasses import dataclass
from PyQt6.QtWidgets import QWidget, QLabel
from PyQt6.QtCore import Qt


T = TypeVar('T')


@dataclass
class FrameData:
    """Stores the data passed to a frame."""
    data: Any = None
    

@runtime_checkable
class Frame(Protocol):
    """Protocol for frame widgets."""
    def __init__(self, title: str, data: Any, *args, **kwargs) -> None:
        ...
    
    @property
    def title(self) -> str:
        """Return the frame title."""
        ...
    
    @property
    def data(self) -> Any:
        """Return the frame data."""
        ...


class FrameBase(QWidget, Generic[T], Frame):
    """Base class for all frame widgets.
    
    This provides the core functionality:
    - Title bar with close button
    - Layout management
    - Type-safe data handling
    - Event filtering
    """
    
    def __init__(self, title: str, data: Any, parent: QWidget | None = None):
        super().__init__(parent)
        
        self._title = title
        self._data = data
        self._frame_data = FrameData(data=data)
        
        # Create the layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create title bar
        self._title_bar = _FrameTitleBar(title)
        layout.addWidget(self._title_bar)
        
        # Create content area
        self._content = QWidget()
        layout.addWidget(self._content)
        
        # Set up event filters
        self._setup_event_filters()
    
    @property
    def title(self) -> str:
        """Return the frame title."""
        return self._title
    
    @property
    def data(self) -> Any:
        """Return the frame data."""
        return self._data
    
    @property
    def frame_data(self) -> FrameData:
        """Return the frame data object."""
        return self._frame_data
    
    def set_data(self, data: Any) -> None:
        """Set new data for the frame."""
        self._data = data
        self._frame_data.data = data
    
    def clear_data(self) -> None:
        """Clear the frame data."""
        self._data = None
        self._frame_data.data = None
    
    def _setup_event_filters(self) -> None:
        """Set up event filters for the frame."""
        self._content.installEventFilter(self)
    
    def eventFilter(self, obj: QWidget, event: Any) -> bool:
        """Override event filtering."""
        return False
    
    def _clear_layout(self) -> None:
        """Clear the content layout."""
        layout = self._content.layout()
        if layout is not None:
            while layout.count() > 0:
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
    
    def _add_widget(self, widget: QWidget) -> None:
        """Add a widget to the content area."""
        self._clear_layout()
        self._content.addWidget(widget)


class _FrameTitleBar(QWidget):
    """Title bar for frame widgets."""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Title label
        self._title_label = QLabel(title)
        self._title_label.setProperty("title", True)
        layout.addWidget(self._title_label)
        
        # Spacer
        layout.addStretch()
        
        # Close button
        self._close_button = QCloseHandler(self)
        layout.addWidget(self._close_button)
    
    @property
    def title(self) -> str:
        return self._title


class QCloseHandler(QLabel):
    """A QLabel that acts as a close button.
    
    Uses a stylized 'X' character with custom cursor.
    """
    
    def __init__(self, parent=None):
        super().__init__("&times", parent)
        self.setProperty("closeButton", True)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setObjectName("closeButton")
        
        # Make the label act as a button
        self.setContentsMargins(0, 0, 0, 0)
        self.setFixedHeight(18)
