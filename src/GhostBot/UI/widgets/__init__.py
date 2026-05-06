#!/usr/bin/env python3
"""PyQt6 UI components for GhostBot.

This module provides a modern, type-safe replacement for the tkinter-based
GhostBot UI with improved layout management, theming, and state handling.
"""

from __future__ import annotations

import typing
from typing import TYPE_CHECKING, TypeVar, Generic, Protocol

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import Qt, QAbstractItemModel, pyqtSignal, QAbstractListModel, QModelIndex


class FrameVariables(Protocol):
    """Protocol for objects that expose named variables (FrameVariables)."""
    
    def getvar(self, name: str) -> str | bool | int | float | None:
        """Get the value of a variable by name."""
        ...
    
    def setvar(self, name: str, value: str | bool | int | float | None) -> None:
        """Set the value of a variable by name."""
        ...


T = TypeVar('T')


class FrameVariable(Generic[T]):
    """A strongly-typed variable widget for use in PyQt6 frames.
    
    This wraps a PyQt6 widget (QLineEdit, QCheckBox, QSpinBox, QDoubleSpinBox) and
    provides a type-safe interface to get/set values with automatic conversion.
    """
    
    def __init__(
        self,
        parent: QWidget | None = None,
        name: str = "",
        value: T = None,
        widget_type: type[QWidget] | None = None,
        on_changed: typing.Callable[[T], typing.Any] | None = None,
    ):
        self.name = name
        self._value: T = value
        self._on_changed = on_changed
        
        # Create the appropriate widget based on type
        if widget_type is not None:
            self._widget = widget_type(parent)
        elif isinstance(value, bool):
            self._widget = QCheckBox(parent)
            self._widget.setChecked(bool(value))
            self._widget.stateChanged.connect(self._on_value_changed)
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                self._widget = QDoubleSpinBox(parent)
                self._widget.setValue(float(value))
                self._widget.setDecimals(2)
            else:
                self._widget = QSpinBox(parent)
                self._widget.setValue(int(value))
            self._widget.valueChanged.connect(self._on_value_changed)
        elif isinstance(value, str):
            self._widget = QLineEdit(parent)
            self._widget.setText(str(value))
            self._widget.textChanged.connect(self._on_value_changed)
        else:
            self._widget = QLineEdit(parent)
            self._widget.setText(str(value) if value is not None else "")
            self._widget.textChanged.connect(self._on_value_changed)
        
        self._on_value_changed.connect(self._on_value_changed)
    
    @property
    def widget(self) -> QWidget:
        """Get the underlying widget."""
        return self._widget
    
    def get_value(self) -> T:
        """Get the current value."""
        return self._value
    
    def set_value(self, value: T) -> None:
        """Set the value and update the widget."""
        self._value = value
        if isinstance(value, bool):
            self._widget.setChecked(bool(value))
        elif isinstance(value, (int, float)):
            if isinstance(value, float):
                self._widget.setValue(float(value))
            else:
                self._widget.setValue(int(value))
        else:
            self._widget.setText(str(value) if value is not None else "")
        
        # Emit signal if there's a handler
        if self._on_changed:
            self._on_changed(value)
    
    def _on_value_changed(self, new_value: typing.Any) -> None:
        """Handle widget value changes."""
        if self._on_changed:
            self._on_changed(new_value)
        
        # Update our internal value
        if isinstance(self._widget, QCheckBox):
            self._value = bool(self._widget.isChecked())
        elif isinstance(self._widget, (QSpinBox, QDoubleSpinBox)):
            self._value = float(self._widget.value()) if isinstance(self._value, float) else int(self._widget.value())
        else:
            self._value = self._widget.text()
    
    def clear(self) -> None:
        """Clear the widget (reset to default state)."""
        if isinstance(self._widget, QCheckBox):
            self._widget.setChecked(False)
            self._value = False
        elif isinstance(self._widget, (QSpinBox, QDoubleSpinBox)):
            self._widget.setValue(0)
            self._value = 0
        else:
            self._widget.clear()
            self._value = None


class FrameVariablesContainer(Generic[T]):
    """A container for FrameVariables that can be used as a base class for PyQt6 frames.
    
    This provides a simple way to manage multiple variables within a frame,
    with automatic serialization and deserialization.
    """
    
    _variables: dict[str, FrameVariable[T]]
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._variables: dict[str, FrameVariable[T]] = {}
    
    def add_variable(
        self,
        name: str,
        value: T = None,
        widget_type: type[QWidget] | None = None,
        on_changed: typing.Callable[[T], typing.Any] | None = None,
    ) -> FrameVariable[T]:
        """Add a new variable to the container."""
        var = FrameVariable(
            parent=self,
            name=name,
            value=value,
            widget_type=widget_type,
            on_changed=on_changed,
        )
        self._variables[name] = var
        return var
    
    def getvar(self, name: str) -> T:
        """Get the value of a variable by name."""
        if name not in self._variables:
            raise AttributeError(f"No variable named '{name}'")
        return self._variables[name].get_value()
    
    def setvar(self, name: str, value: T) -> None:
        """Set the value of a variable by name."""
        if name not in self._variables:
            raise AttributeError(f"No variable named '{name}'")
        self._variables[name].set_value(value)
    
    def getall(self) -> dict[str, T]:
        """Get all variable values."""
        return {name: var.get_value() for name, var in self._variables.items()}
    
    def setall(self, values: dict[str, T]) -> None:
        """Set all variable values from a dictionary."""
        for name, value in values.items():
            if name in self._variables:
                self._variables[name].set_value(value)
    
    def clear(self) -> None:
        """Clear all variables (reset to default state)."""
        for var in self._variables.values():
            var.clear()
    
    def variables(self) -> typing.Iterator[FrameVariable[T]]:
        """Iterate over all variables."""
        return self._variables.values()
    
    def __iter__(self) -> typing.Iterator[str]:
        """Iterate over variable names."""
        return iter(self._variables)
    
    def __contains__(self, name: str) -> bool:
        """Check if a variable exists."""
        return name in self._variables
    
    def __len__(self) -> int:
        """Return the number of variables."""
        return len(self._variables)
