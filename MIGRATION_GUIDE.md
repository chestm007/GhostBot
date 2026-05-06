# PyQt6 Migration Guide for GhostBot UI

## Overview
This guide outlines the migration from tkinter to PyQt6 for GhostBot's UI implementation.

## Quick Comparison

| Feature | tkinter | PyQt6 |
|---------|---------|--------|
| Layout Manager | `.place()`, `.pack()`, `.grid()` | `QVBoxLayout`, `QHBoxLayout`, `QGridLayout` |
| State Management | `tk.Variable`, `ttk.Treeview` | `QAbstractItemModel`, `QAbstractTableModel` |
| Styling | Manual color values | QSS (Stylesheets) |
| List View | `tk.Listbox` | `QListView` with `QAbstractItemModel` |
| Tab Widget | `ttk.Notebook` | `QTabWidget` (with drag-drop support) |
| Logging | `tk.Text` | `QPlainTextEdit` |

## Migration Strategy

### Phase 1: Core Application Structure

**Current** (tkinter):
```python
from tkinter import Tk, ttk

class GhostBot(Tk):
    def __init__(self):
        super().__init__()
        self.title("GhostBot")
        self.geometry("700x490")
        
        self.list_box = ScrollableListbox(...)
        self.list_box.place(x=7, y=9, width=163, height=439)
        
        self.tabbed_widget = TabbedWidget(...)
        self.tabbed_widget.place(x=177, y=9, width=508, height=230)
```

**PyQt6**:
```python
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt

class GhostBotApp(QApplication):
    def __init__(self):
        super().__init__(sys.argv)
        
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("GhostBot")
        
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        
        # Frame with layout managers
        main_frame = QFrame()
        frame_layout = QVBoxLayout(main_frame)
```

### Phase 2: Character List Widget

**Current** (tkinter):
```python
class ScrollableListbox(tk.Listbox):
    def __init__(self, parent, scrollx=False, scrolly=True, listvariable=None):
        super().__init__(parent)
        if scrolly:
            frame = tk.Frame(parent)
            self.canvas = tk.Canvas(frame)
            self.scrollbar = tk.Scrollbar(frame, orient="vertical")
            ...
```

**PyQt6**:
```python
class CharacterListView(QListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setAlternatingRowColors(True)
        self.setWrapAround(False)
        self.setFlow(QListView.LeftToRight)
        self.setMovement(QAbstractItemView.Static)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        self.doubleClicked.connect(self.on_double_click)
        self.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.setModel(CharacterListModel(self))
```

### Phase 3: Tabbed Widget with Reorder

**Current** (tkinter):
```python
class TabbedWidget(ttk.Notebook):
    def __init__(self, master=None, enable_reorder=False):
        super().__init__(master)
        if enable_reorder:
            self.bind("<B1-Motion>", self.reorder)
    
    def reorder(self, event):
        try:
            index = self.index(f"@{event.x},{event.y}")
            self.insert(index, child=self.select())
        except tk.TclError:
            pass
```

**PyQt6**:
```python
class ReorderableTabWidget(QTabWidget):
    def __init__(self, parent=None, enable_reorder=False):
        super().__init__(parent)
        
        # Enable drag-and-drop reordering
        self.setMovable(enable_reorder)
        self.tabBar().setTabBarAutoHide(False)
```

### Phase 4: Frame Base Class

**Current** (tkinter):
```python
class TabFrame(tk.Frame, ABC):
    def __init__(self, master, *args, **kwargs):
        super().__init__(master)
        self.config(bg="#EDECEC", width=650, height=459)
        self._init(*args, **kwargs)
```

**PyQt6**:
```python
class FrameVariablesContainer(QFrame, Generic[T]):
    _variables: dict[str, FrameVariable[T]]
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._variables: dict[str, FrameVariable[T]] = {}
    
    def add_variable(
        self,
        name: str,
        value: T = None,
        widget_type: type[QWidget] | None = None,
    ) -> FrameVariable[T]:
        var = FrameVariable(
            parent=self,
            name=name,
            value=value,
            widget_type=widget_type,
        )
        self._variables[name] = var
        return var
    
    def getvar(self, name: str) -> T:
        if name not in self._variables:
            raise AttributeError(f"No variable named '{name}'")
        return self._variables[name].get_value()
    
    def setvar(self, name: str, value: T) -> None:
        if name not in self._variables:
            raise AttributeError(f"No variable named '{name}'")
        self._variables[name].set_value(value)
```

## Benefits of PyQt6 Migration

1. **Type Safety**: Full type hints with IDE support
2. **Modern Styling**: QSS makes theming much easier than hardcoded colors
3. **Better Layout Management**: Layout managers are more robust than `.place()`
4. **Cross-platform**: Works on Linux, macOS, and Windows (not just Windows)
5. **Performance**: Faster than tkinter for complex UIs
6. **Ecosystem**: Access to Qt's extensive widget library
7. **Better State Management**: `QAbstractItemModel` for complex data structures

## Migration Checklist

- [ ] Install PyQt6: `pip install PyQt6 PyQt6-Tools`
- [ ] Create new `UI/` directory structure
- [ ] Migrate `ScrollableListbox` to `CharacterListView`
- [ ] Migrate `TabbedWidget` to `ReorderableTabWidget`
- [ ] Migrate `LogWindow` to `QPlainTextEdit`
- [ ] Migrate `TabFrame` to `FrameVariablesContainer`
- [ ] Update all `.place()` calls to use layout managers
- [ ] Replace hardcoded colors with QSS stylesheets
- [ ] Migrate state variables to `FrameVariable`
- [ ] Test all functionality
- [ ] Update documentation

## Next Steps

Let me create the actual PyQt6 components for you.
