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
        self.label.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
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
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333333;
                    color: #e0e0e0;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:checked {
                    background-color: #a6e3a1;
                    color: #1e1e1e;
                }
                QPushButton:hover:!checked {
                    background-color: #444444;
                }
            """)
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
