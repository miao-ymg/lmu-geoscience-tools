from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QPalette, QPainter, QPolygonF
from PyQt6.QtCore import QPointF
import math

class AnimatedProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._maximum = 100
        self._indeterminate = False
        self._offset = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(30) # ~33 fps
        self.setFixedHeight(8)
        
    def update_animation(self):
        self._offset += 1
        if self._offset > 40:
            self._offset = 0
        self.update()
        
    def setRange(self, min_val, max_val):
        if min_val == 0 and max_val == 0:
            self._indeterminate = True
        else:
            self._indeterminate = False
            self._maximum = max_val
            
    def setValue(self, val):
        self._value = val
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Draw background
        painter.setBrush(QColor("#444444"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        
        # Calculate width of the chunk
        if self._indeterminate:
            # Bouncing block logic
            chunk_width = rect.width() * 0.3
            progress = (math.sin(self._offset / 40.0 * math.pi * 2) + 1) / 2
            x = progress * (rect.width() - chunk_width)
            chunk_rect = QRectF(x, 0, chunk_width, rect.height())
        else:
            if self._maximum <= 0: return
            width = (self._value / self._maximum) * rect.width()
            chunk_rect = QRectF(0, 0, width, rect.height())
            
        if chunk_rect.width() <= 0: return
            
        # Create a rounded path for the chunk to clip both base color and stripes
        from PyQt6.QtGui import QPainterPath
        clip_path = QPainterPath()
        clip_path.addRoundedRect(chunk_rect, 4, 4)
        painter.setClipPath(clip_path)
        
        base_color = QColor("#a6e3a1")
        stripe_color = QColor("#89d084") # slightly darker green
        
        # Base color of the chunk
        painter.setBrush(base_color)
        painter.drawPath(clip_path)
        
        # Draw stripes
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(stripe_color)
        stripe_width = 20
        
        # Animate the offset of stripes
        shift = (self._offset / 40.0) * (stripe_width * 2)
        
        slant = 15
        for i in range(-int(rect.width()), int(rect.width()) * 2, stripe_width * 2):
            x1 = i + shift
            x2 = x1 + stripe_width
            
            poly = [
                (x1, 0),
                (x2, 0),
                (x2 - slant, rect.height()),
                (x1 - slant, rect.height())
            ]
            
            qpoly = QPolygonF([QPointF(px, py) for px, py in poly])
            painter.drawPolygon(qpoly)

class StartupOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Block mouse events from reaching underneath
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Solid background matching the rest of the app
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30, 255))
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("LMU Geoscience Tools")
        title.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Initializing application...")
        self.status_label.setStyleSheet("color: #a0a0a0; font-size: 14px; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedWidth(400)
        
        layout.addWidget(title)
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.status_label)
        
    def update_progress(self, value, text):
        self.progress_bar.setValue(value)
        self.status_label.setText(text)
        
    def resizeEvent(self, event):
        # Always cover the entire parent
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)


class PanelOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Block mouse events for the local panel
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Solid background matching the rest of the app
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 30, 255))
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = QLabel("Processing data and generating plot...")
        self.status_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.progress_bar.setFixedWidth(250)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignHCenter)
