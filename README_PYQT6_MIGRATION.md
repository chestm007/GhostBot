# GhostBot UI Migration Guide

This guide explains how to migrate GhostBot's tkinter-based UI to PyQt6, providing a modern, cross-platform alternative while maintaining type safety and better layout management.

## Table of Contents

- [Why Migrate?](#why-migrate)
- [Migration Comparison](#migration-comparison)
- [Code Migration Examples](#code-migration-examples)
- [Migration Checklist](#migration-checklist)
- [Benefits Analysis](#benefits-analysis)
- [Step-by-Step Migration](#step-by-step-migration)

---

## Why Migrate?

The current tkinter-based UI has several limitations:

- **Windows-only**: tkinter works best on Windows, making GhostBot Windows-only
- **Rigid geometry**: Uses `.place()` with hardcoded coordinates rather than layouts
- **No type safety**: Uses `tk.Variable` instead of typed state management
- **Limited styling**: Custom widget styling is complex and inconsistent
- **No modern features**: Drag-drop, smooth animations, theme support are absent

## Migration Comparison

| Feature | tkinter | PyQt6 |
|---------|---------|-------|
| Layouts | `.place()` (rigid) | `QVBoxLayout`, `QGridLayout` (flexible) |
| State Management | `tk.Variable` | `QAbstractTableModel`, dataclasses |
| Styling | `.config()` (basic) | QSS (Qt Style Sheets) |
| Cross-platform | Windows-only | Linux, macOS, Windows |
| Type Safety | Optional | Full (Pydantic, typing) |
| Multi-selection | `.curselection()` | `QAbstractItemView.SelectionMode` |
| Drag-drop | Not supported | Native support |
| High DPI | Limited | Native support |

## Code Migration Examples

### Window Creation

**tkinter:**
```python
def __init__(self):
    super().__init__()
    self.title("GhostBot")
    self.config(bg="#545454")
    self.geometry("700x490")
```

**PyQt6:**
```python
def __init__(self):
    super().__init__()
    self.setWindowTitle("GhostBot")
    self.setStyleSheet("QWidget { background-color: #1a1a1a; }")
    self.setGeometry(100, 100, 800, 600)
```

### Layout Management

**tkinter:**
```python
self.list_box.place(x=7, y=9, width=163, height=439)
self.tabbed_widget.place(x=177, y=9, width=508, height=230)
```

**PyQt6:**
```python
layout = QVBoxLayout(self)
list_view = QListView(self)
list_view.setFixedWidth(163)
list_view.setFixedHeight(439)
layout.addWidget(list_view)
```

### State Management

**tkinter:**
```python
self._char_list = tk.Variable(master=self)
self.client.add_callback(Command.INFO, lambda message: self.set_char_list(message.target.split(' ')))

def set_char_list(self, _char_list):
    if self._char_list.get() != _char_list:
        self._char_list.set(_char_list)
```

**PyQt6:**
```python
model = CharacterListModel(self)
model.set_characters(char_list, data={})
list_view.setModel(model)

def update_characters(self, char_list, data=None):
    model.set_characters(char_list, data)
```

### Styling

**tkinter:**
```python
self.list_box.config(bg="#646464", fg="#eaeaea")
```

**PyQt6:**
```python
list_view.setStyleSheet("""
    QListView {
        background-color: #646464;
        color: #eaeaea;
        border: 1px solid #404040;
        border-radius: 4px;
    }
    QListView::item:selected {
        background-color: #4ec9b0;
    }
""")
```

## Migration Checklist

- [x] Create PyQt6 main window with dark theme
- [x] Implement character list view with multi-selection
- [x] Implement tabbed widget with reordering
- [x] Implement log window with auto-scroll
- [x] Implement attack/buff/fairy frames
- [ ] Migrate remaining frame components
- [ ] Migrate menu bar and file operations
- [ ] Migrate settings persistence
- [ ] Write migration tests
- [ ] Update documentation

## Benefits Analysis

### Advantages of PyQt6

1. **Cross-platform**: Works on Linux, macOS, and Windows natively
2. **Type safety**: Full type hints with Pydantic dataclasses
3. **Modern layouts**: QLayout system provides flexible, responsive UI
4. **Better styling**: QSS (Qt Style Sheets) with CSS-like syntax
5. **Performance**: Better for large lists and complex UI
6. **Accessibility**: Built-in accessibility support
7. **High DPI**: Native support for retina displays

### Trade-offs

1. **Learning curve**: PyQt6 has a steeper learning curve than tkinter
2. **Dependencies**: Requires PyQt6 (or PySide6) installation
3. **Code size**: PyQt6 code tends to be more verbose
4. **Event loop**: Must use `app.exec()` instead of `mainloop()`

## Step-by-Step Migration

### Phase 1: Setup

1. Install PyQt6:
```bash
pip install PyQt6 pydantic
```

2. Create main application class:
```python
from PyQt6.QtWidgets import QApplication
import sys

app = QApplication(sys.argv)
window = create_main_window()
window.show()
sys.exit(app.exec())
```

### Phase 2: Create Components

3. Implement `QListView` for character selection
4. Implement `QTabWidget` for the main content area
5. Implement `QPlainTextEdit` for logs
6. Implement frame widgets for attack/buff/fairy

### Phase 3: Wire Up Logic

7. Connect IPC callbacks to PyQt6 signals
8. Replace `.place()` with `QLayout.addWidget()`
9. Replace `tk.Variable` with `QAbstractTableModel`
10. Migrate all existing frame components

### Phase 4: Testing

11. Test on Windows (current platform)
12. Test on Linux (if available)
13. Test with high DPI displays
14. Performance test with large character lists

### Phase 5: Documentation

15. Document all PyQt6-specific APIs
16. Create migration examples
17. Update README with PyQt6 information
18. Write user guide for PyQt6 features

---

## Next Steps

The migration is complete for the core components. The remaining work includes:

1. **Migrate remaining frames**: pet, regen, sell, delete
2. **Implement menu bar**: File, Help menus
3. **Add settings persistence**: QSettings for window geometry
4. **Write comprehensive tests**: PyQt6 QTest framework
5. **Performance optimization**: Lazy loading for large lists
6. **Theme customization**: User theme support

All migration components are now available in the `src/GhostBot/UI/` directory.
