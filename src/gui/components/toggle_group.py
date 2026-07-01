from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup
from PyQt6.QtCore import Qt, pyqtSignal

class ToggleGroup(QWidget):
    selectionChanged = pyqtSignal(str)
    
    def __init__(self, label_text, options, default_option=None):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.label = QLabel(label_text)
        self.label.setObjectName("ToggleGroupLabel")
        self.layout.addWidget(self.label)
        
        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.button_group = QButtonGroup(self)
        
        self.update_options(options, default_option)
        
        self.buttons_layout.addStretch()
        self.layout.addLayout(self.buttons_layout)
        
    def update_options(self, options, default_option=None):
        # Remove old buttons
        for btn in self.button_group.buttons():
            self.button_group.removeButton(btn)
            self.buttons_layout.removeWidget(btn)
            btn.deleteLater()
            
        for val in options:
            btn = QPushButton(val)
            btn.setObjectName("ToggleBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if val == default_option:
                btn.setChecked(True)
            
            self.button_group.addButton(btn)
            
            # Insert before the stretch if it exists
            count = self.buttons_layout.count()
            if count > 0 and self.buttons_layout.itemAt(count - 1).spacerItem():
                self.buttons_layout.insertWidget(count - 1, btn)
            else:
                self.buttons_layout.addWidget(btn)
                
        # Reconnect signal safely
        try:
            self.button_group.buttonClicked.disconnect()
        except TypeError:
            pass
        self.button_group.buttonClicked.connect(lambda btn: self.selectionChanged.emit(btn.text()))
