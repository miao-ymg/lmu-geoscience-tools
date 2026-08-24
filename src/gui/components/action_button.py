from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import pyqtSignal, QVariantAnimation, Qt
from theme import colors, hex_to_rgb

class ActionButton(QPushButton):
    def __init__(self, text, style_type="primary", font_size=14, font_weight=600, parent=None):
        super().__init__(text, parent)
        self.style_type = style_type
        self.font_size = font_size
        self.font_weight = font_weight
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(150)
        self.anim.valueChanged.connect(self._on_anim_value)
        self.current_hover = 0.0
        
        self.toggled.connect(lambda _: self.update_style()) if hasattr(self, 'toggled') else None
        self.update_style()
        
    def changeEvent(self, event):
        from PyQt6.QtCore import QEvent
        if event.type() == QEvent.Type.EnabledChange:
            self.update_style()
        super().changeEvent(event)
        
    def enterEvent(self, event):
        if not self.isEnabled(): return super().enterEvent(event)
        self.anim.stop()
        self.anim.setStartValue(self.current_hover)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        if not self.isEnabled(): return super().leaveEvent(event)
        self.anim.stop()
        self.anim.setStartValue(self.current_hover)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)
        
    def _on_anim_value(self, val):
        self.current_hover = val
        self.update_style()
        
    def update_style(self):
        if not self.isEnabled():
            bg = hex_to_rgb(colors["bg-btn-disabled"])
            r, g, b = bg
            text_color = colors["text-btn-disabled"]
            border = colors["border-btn-disabled"]
        elif self.style_type == "primary":
            base = hex_to_rgb(colors["anim-btn-primary-base-bg"])
            hover = hex_to_rgb(colors["anim-btn-primary-hover-bg"])
            
            r = int(base[0] + (hover[0] - base[0]) * self.current_hover)
            g = int(base[1] + (hover[1] - base[1]) * self.current_hover)
            b = int(base[2] + (hover[2] - base[2]) * self.current_hover)
            border = colors["anim-btn-primary-base-border"] # Or interpolate this too if needed
            text_color = colors["text-white"]
        else: # secondary
            base = hex_to_rgb(colors["anim-btn-secondary-base-bg"])
            hover = hex_to_rgb(colors["anim-btn-secondary-hover-bg"])
            
            r = int(base[0] + (hover[0] - base[0]) * self.current_hover)
            g = int(base[1] + (hover[1] - base[1]) * self.current_hover)
            b = int(base[2] + (hover[2] - base[2]) * self.current_hover)
            border = colors["anim-btn-secondary-base-border"]
            text_color = colors["text-main"]
            
        self.setStyleSheet(f"""
            QPushButton {{ 
                background-color: rgb({r}, {g}, {b}); 
                color: {text_color}; 
                font-family: "IBM Plex Sans", sans-serif;
                font-size: {self.font_size}px; 
                font-weight: {self.font_weight}; 
                padding: 15px; 
                border-radius: 8px; 
                border: 1px solid {border}; 
            }}
        """)
