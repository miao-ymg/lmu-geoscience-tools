from PyQt6.QtWidgets import QStyledItemDelegate
from PyQt6.QtCore import QObject, QRect, QRectF, pyqtProperty, pyqtSignal, QVariantAnimation, Qt
from PyQt6.QtGui import QPainter, QColor, QFont

class SlidingAnimator(QObject):
    rectChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rect = QRectF()
        
    @pyqtProperty(QRectF)
    def rect(self):
        return self._rect
        
    @rect.setter
    def rect(self, value):
        self._rect = value
        self.rectChanged.emit()


class SidebarDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_opacities = {}  
        self.hover_anims = {}      
        self.sliding_rect = QRectF()
        self.hover_blocked = False
        self.instant_white_row = -1
        
        self.bg_active = QColor("#232f22")
        self.bg_hover = QColor("#1c232c")
        self.text_dim = QColor("#8c9baa")
        self.text_main = QColor("#e2f0e4")
        
    def set_sliding_rect(self, rect: QRectF):
        self.sliding_rect = rect
        if self.parent():
            self.parent().viewport().update()

    def clear_hovers(self):
        for anim in self.hover_anims.values():
            anim.stop()
        self.hover_anims.clear()
        self.hover_opacities.clear()
        if self.parent():
            self.parent().viewport().update()

    def unblock_hover(self):
        self.hover_blocked = False

    def update_hover(self, row: int, hovered: bool):
        if self.hover_blocked and hovered:
            return
            
        if row not in self.hover_opacities:
            self.hover_opacities[row] = 0.0
            
        current_val = self.hover_opacities[row]
        target_val = 1.0 if hovered else 0.0
        
        if current_val == target_val:
            return
            
        if row in self.hover_anims:
            self.hover_anims[row].stop()
            
        anim = QVariantAnimation(self)
        anim.setStartValue(current_val)
        anim.setEndValue(target_val)
        # Faster fade out (dehover) than fade in
        anim.setDuration(150 if hovered else 50)
        
        def on_val_changed(val, r=row):
            self.hover_opacities[r] = val
            if self.parent():
                self.parent().viewport().update()
                
        anim.valueChanged.connect(on_val_changed)
        anim.start()
        self.hover_anims[row] = anim

    def paint(self, painter: QPainter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        row = index.row()
        rect = QRectF(option.rect)
        
        # Margin matching QSS: 2px 14px 2px 14px
        item_rect = rect.adjusted(14, 2, -14, -2)
        
        # 1. Draw Hover Background
        hover_opacity = self.hover_opacities.get(row, 0.0)
        if hover_opacity > 0:
            c = QColor(self.bg_hover)
            c.setAlphaF(hover_opacity)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            painter.drawRoundedRect(item_rect, 6, 6)
            
        # 2. Draw Sliding Green Rectangle
        if self.sliding_rect.isValid() and item_rect.intersects(self.sliding_rect):
            painter.setClipRect(rect)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(self.bg_active)
            painter.drawRoundedRect(self.sliding_rect, 6, 6)
            painter.setClipping(False)
            
        # 3. Draw Text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            factor = 0.0
            if self.sliding_rect.isValid():
                dist = abs(item_rect.center().y() - self.sliding_rect.center().y())
                max_dist = item_rect.height()
                factor = max(0.0, 1.0 - (dist / max_dist))
                
            text_factor = max(hover_opacity, factor)
            
            if row == self.instant_white_row:
                text_factor = 1.0
            
            r = int(self.text_dim.red() + (self.text_main.red() - self.text_dim.red()) * text_factor)
            g = int(self.text_dim.green() + (self.text_main.green() - self.text_dim.green()) * text_factor)
            b = int(self.text_dim.blue() + (self.text_main.blue() - self.text_dim.blue()) * text_factor)
            
            painter.setPen(QColor(r, g, b))
            
            # Font handling
            font = QFont("IBM Plex Sans", 15)
            font.setWeight(QFont.Weight.Medium)
            painter.setFont(font)
            
            # Padding-left: 12px
            text_rect = item_rect.adjusted(12, 0, -12, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
            
        painter.restore()
