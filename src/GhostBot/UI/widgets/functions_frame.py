#!/usr/bin/env python3
"""PyQt6 FunctionsFrame for GhostBot UI migration."""

from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                            QCheckBox, QLabel, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt


class FunctionsFrame(QFrame):
    """Functions frame with checkboxes for bot configuration."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("functionsFrame")
        self.setFixedHeight(459)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create left column for checkboxes
        left_layout = QVBoxLayout()
        
        self._attack_enabled = QCheckBox("Attack", self)
        self._fairy_enabled = QCheckBox("Fairy", self)
        self._buff_enabled = QCheckBox("Buff", self)
        self._regen_enabled = QCheckBox("Regen", self)
        self._pet_enabled = QCheckBox("Pet", self)
        self._sell_enabled = QCheckBox("Sell", self)
        self._delete_enabled = QCheckBox("Delete", self)
        
        left_layout.addWidget(self._attack_enabled)
        left_layout.addWidget(self._fairy_enabled)
        left_layout.addWidget(self._buff_enabled)
        left_layout.addWidget(self._regen_enabled)
        left_layout.addWidget(self._pet_enabled)
        left_layout.addWidget(self._sell_enabled)
        left_layout.addWidget(self._delete_enabled)
        
        # Create right column for character info
        right_layout = QFormLayout()
        right_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Character info variables
        self._char_vars = {
            'name': QLabel("Name:"),
            'level': QLabel("Level:"),
            'location': QLabel("Location:"),
            'hp': QLabel("HP:"),
            'mana': QLabel("Mana:"),
            'target_name': QLabel("Target Name:"),
            'target_hp': QLabel("Target HP:"),
            'pos': QLabel("Pos:"),
            'status': QLabel("Status:"),
        }
        
        # Character info value labels
        self._info_labels = {
            'name': QLabel("loading.", self),
            'level': QLabel("loading.", self),
            'location': QLabel("loading.", self),
            'hp': QLabel("loading.", self),
            'mana': QLabel("loading.", self),
            'target_name': QLabel("loading.", self),
            'target_hp': QLabel("loading.", self),
            'pos': QLabel("loading.", self),
            'status': QLabel("loading.", self),
        }
        
        # Set labels (not value labels)
        for key in ['name', 'level', 'location', 'hp', 'mana', 'target_name', 
                    'target_hp', 'pos', 'status']:
            right_layout.addRow(self._char_vars[key], self._info_labels[key])
        
        # Set initial values
        self._info_labels['name'].setText("loading.")
        self._info_labels['level'].setText("loading.")
        self._info_labels['location'].setText("loading.")
        self._info_labels['hp'].setText("loading.")
        self._info_labels['mana'].setText("loading.")
        self._info_labels['target_name'].setText("loading.")
        self._info_labels['target_hp'].setText("loading.")
        self._info_labels['pos'].setText("loading.")
        self._info_labels['status'].setText("loading.")
        
        # Create main layout with two columns
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 1)
    
    @property
    def attack_enabled(self) -> QCheckBox:
        return self._attack_enabled
    
    @property
    def fairy_enabled(self) -> QCheckBox:
        return self._fairy_enabled
    
    @property
    def buff_enabled(self) -> QCheckBox:
        return self._buff_enabled
    
    @property
    def regen_enabled(self) -> QCheckBox:
        return self._regen_enabled
    
    @property
    def pet_enabled(self) -> QCheckBox:
        return self._pet_enabled
    
    @property
    def sell_enabled(self) -> QCheckBox:
        return self._sell_enabled
    
    @property
    def delete_enabled(self) -> QCheckBox:
        return self._delete_enabled
    
    def set_var(self, key: str, value: str) -> None:
        """Set a character info variable."""
        if key in self._info_labels:
            self._info_labels[key].setText(value)
    
    def get_var(self, key: str) -> str:
        """Get a character info variable."""
        if key in self._info_labels:
            return self._info_labels[key].text()
        return ""
