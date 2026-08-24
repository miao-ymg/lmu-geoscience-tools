from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QColor, QPalette, QPainter
from PyQt6.QtCore import QPointF
import math
from theme import colors

class AnimatedEllipsisLabel(QLabel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._base_text = ""
        self._dots = 1
        self._has_ellipsis = False
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_dots)
        self.timer.start(600)
        
    def setText(self, text):
        if text.endswith("..."):
            self._has_ellipsis = True
            self._base_text = text[:-3]
        else:
            self._has_ellipsis = False
            self._base_text = text
        self.update_display()
            
    def update_dots(self):
        if self._has_ellipsis:
            self._dots = (self._dots % 3) + 1
            self.update_display()
            
    def update_display(self):
        if self._has_ellipsis:
            dots_str = "." * self._dots
            # Ensure it takes up the same space by padding with invisible characters or just let it resize
            # A fixed width might be better, but we'll just update the text
            super().setText(self._base_text + dots_str)
        else:
            super().setText(self._base_text)

class AnimatedProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0
        self._display_value = 0.0
        self._maximum = 100
        self._indeterminate = False
        self._pulse_frame = 0
        
        self.setFixedHeight(8)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16) # ~60 fps
        
    def setRange(self, min_val, max_val):
        if min_val == 0 and max_val == 0:
            self._indeterminate = True
            self._maximum = 100
        else:
            self._indeterminate = False
            self._maximum = max_val
            
    def setValue(self, val):
        self._value = val
        
    def update_animation(self):
        self._pulse_frame += 1
        
        if self._indeterminate:
            if self._display_value < 95:
                self._display_value += 0.2
            self.update()
        else:
            diff = self._value - self._display_value
            if abs(diff) > 0.1:
                self._display_value += diff * 0.1
                self.update()
            elif self._display_value != self._value:
                self._display_value = self._value
                self.update()
            else:
                # Still need to update for the pulse effect
                self.update()
            
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Track background
        painter.setBrush(QColor("#1C212B"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, 4, 4)
        
        if self._maximum <= 0: return
        
        width = (self._display_value / self._maximum) * rect.width()
        chunk_rect = QRectF(0, 0, width, rect.height())
        
        if chunk_rect.width() <= 0: return
            
        # pulse happens every 300 frames (5 seconds), and lasts for 150 frames (2.5 seconds)
        cycle_length = 300
        pulse_duration = 150
        
        # Trigger pulse at the end of the cycle so the first one doesn't happen immediately
        frame_in_cycle = self._pulse_frame % cycle_length
        if frame_in_cycle > (cycle_length - pulse_duration):
            progress_in_pulse = (frame_in_cycle - (cycle_length - pulse_duration)) / pulse_duration
            # Smooth bell curve (0 -> 1 -> 0) with zero derivatives at ends
            pulse = 0.5 - 0.5 * math.cos(progress_in_pulse * 2 * math.pi)
            factor = 100 + int(35 * pulse)
        else:
            factor = 100
            
        color = QColor(colors["text-accent"]).lighter(factor)
        
        painter.setBrush(color)  
        painter.drawRoundedRect(chunk_rect, 4, 4)

class StartupOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        if parent:
            parent.installEventFilter(self)
            self.resize(parent.size())
        
        # Solid background matching the rest of the app
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(22, 27, 34)) # #161B22
        self.setPalette(palette)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title = QLabel("LMU Geoscience Tools")
        title.setObjectName("LoadingStartupTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = AnimatedEllipsisLabel("Initializing application...")
        self.status_label.setObjectName("LoadingStartupStatus")
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
        if self.parent():
            self.resize(self.parent().size())
        super().resizeEvent(event)

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == event.Type.Resize:
            self.resize(obj.size())
        return super().eventFilter(obj, event)

class PanelOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        
        # Transparent background
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.status_label = AnimatedEllipsisLabel("Processing data and generating plot...")
        self.status_label.setObjectName("LoadingPanelStatus")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.progress_bar = AnimatedProgressBar()
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        self.progress_bar.setFixedWidth(250)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar, 0, Qt.AlignmentFlag.AlignHCenter)

    def showEvent(self, event):
        self.progress_bar._display_value = 0.0
        super().showEvent(event)
