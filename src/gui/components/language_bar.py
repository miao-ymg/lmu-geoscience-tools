from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QIcon, QPixmap
from utils.i18n import i18n
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class LanguageBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LanguageContainer")
        self.setMouseTracking(True)
        
        # Target flag size
        self.flag_w = 32
        self.flag_h = 18
        self.btn_padding = 6
        
        # Exact button dimensions: exact flag size + equal 6px padding all 4 ways
        self.btn_width = self.flag_w + (2 * self.btn_padding)   # 44
        self.btn_height = self.flag_h + (2 * self.btn_padding)  # 30
        self.btn_spacing = 8
        self.btn_radius = 2  # subtle rounding as requested
        
        self.side_margin = 20
        self.top_margin = 16
        self.bottom_margin = 20
        
        # Set fixed height for the bar container
        self.setFixedHeight(self.top_margin + self.btn_height + self.bottom_margin)
        
        # Colors matching sidebar
        self.bg_active = QColor("#232f22")
        self.bg_hover = QColor("#1c232c")
        self.border_sep = QColor("#21262d")
        
        # Pre-scale pixmaps smoothly to avoid aspect-ratio letterboxing inside QIcon
        orig_en = QPixmap(resource_path("resources/icons/EN.png"))
        orig_de = QPixmap(resource_path("resources/icons/DE.png"))
        self.pix_en = orig_en.scaled(
            self.flag_w * 2, self.flag_h * 2, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.pix_de = orig_de.scaled(
            self.flag_w * 2, self.flag_h * 2, 
            Qt.AspectRatioMode.IgnoreAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Rectangles for the two buttons
        y = float(self.top_margin)
        self.rect_en = QRectF(float(self.side_margin), y, float(self.btn_width), float(self.btn_height))
        self.rect_de = QRectF(float(self.side_margin + self.btn_width + self.btn_spacing), y, float(self.btn_width), float(self.btn_height))
        
        # Hover state
        self.hovered_lang = None
        
        # Sliding rect property and animation (same 250ms InOutCubic as sidebar)
        current = i18n.get_language()
        self._sliding_rect = QRectF(self.rect_en if current == "en" else self.rect_de)
        
        self.anim = QPropertyAnimation(self, b"sliding_rect")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        i18n.language_changed.connect(self._on_lang_changed)
        
    @pyqtProperty(QRectF)
    def sliding_rect(self):
        return self._sliding_rect
        
    @sliding_rect.setter
    def sliding_rect(self, rect):
        self._sliding_rect = rect
        self.update()
        
    def _on_lang_changed(self, lang):
        target = self.rect_en if lang == "en" else self.rect_de
        self.anim.stop()
        self.anim.setStartValue(self._sliding_rect)
        self.anim.setEndValue(target)
        self.anim.start()
        
    def mouseMoveEvent(self, event):
        pos = event.position()
        old_hover = self.hovered_lang
        if self.rect_en.contains(pos):
            self.hovered_lang = "en"
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        elif self.rect_de.contains(pos):
            self.hovered_lang = "de"
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.hovered_lang = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            
        if old_hover != self.hovered_lang:
            self.update()
        super().mouseMoveEvent(event)
        
    def leaveEvent(self, event):
        if self.hovered_lang is not None:
            self.hovered_lang = None
            self.update()
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            if self.rect_en.contains(pos):
                i18n.set_language("en")
            elif self.rect_de.contains(pos):
                i18n.set_language("de")
        super().mousePressEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        
        # 0. Separator line at the top (exact same style as under "LEHRSTUHL FÜR GEOLOGIE")
        painter.setPen(self.border_sep)
        painter.drawLine(0, 0, self.width(), 0)
        
        # 1. Hover backgrounds (if not currently active)
        active_lang = i18n.get_language()
        if self.hovered_lang == "en" and active_lang != "en":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.bg_hover)
            painter.drawRoundedRect(self.rect_en, self.btn_radius, self.btn_radius)
        elif self.hovered_lang == "de" and active_lang != "de":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.bg_hover)
            painter.drawRoundedRect(self.rect_de, self.btn_radius, self.btn_radius)
            
        # 2. Sliding Active Background (same styling as tool selection, 4px radius)
        if self._sliding_rect.isValid():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.bg_active)
            painter.drawRoundedRect(self._sliding_rect, self.btn_radius, self.btn_radius)
            
        # 3. Draw Flag Icons with exactly equal padding in all 4 directions (6px each)
        flag_en_rect = QRectF(self.rect_en.x() + self.btn_padding, self.rect_en.y() + self.btn_padding, self.flag_w, self.flag_h)
        flag_de_rect = QRectF(self.rect_de.x() + self.btn_padding, self.rect_de.y() + self.btn_padding, self.flag_w, self.flag_h)
        
        painter.drawPixmap(flag_en_rect.toRect(), self.pix_en)
        painter.drawPixmap(flag_de_rect.toRect(), self.pix_de)
        
        painter.end()
