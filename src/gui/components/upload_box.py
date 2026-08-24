import os
import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QFrame, QGraphicsColorizeEffect
from PyQt6.QtCore import Qt, QVariantAnimation
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap, QPainter, QColor, QIcon
from theme import colors
from gui.components.action_button import ActionButton

class UploadIconBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 48)
        icon_path = resource_path(os.path.join("resources", "icons", "upload.svg"))
        self.icon_pixmap = QIcon(icon_path).pixmap(24, 24)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background circle
        painter.setBrush(QColor(colors["bg-upload-icon"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())
        
        # Center the SVG pixmap accounting for High DPI
        pr = self.icon_pixmap.devicePixelRatio()
        pw = self.icon_pixmap.width() / pr
        ph = self.icon_pixmap.height() / pr
        x = int((self.width() - pw) / 2)
        y = int((self.height() - ph) / 2)
        painter.drawPixmap(x, y, self.icon_pixmap)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AnimatedDropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hover_opacity = 0.0
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(150)
        self.anim.valueChanged.connect(self.set_hover_opacity)
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent; border: none;")
        
    def set_hover_opacity(self, val):
        self.hover_opacity = val
        self.update()
        
    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_opacity)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.hover_opacity)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_base = QColor(colors["bg-upload"])
        bg_hover = QColor(colors["bg-upload-hover"])
        r = int(bg_base.red() + (bg_hover.red() - bg_base.red()) * self.hover_opacity)
        g = int(bg_base.green() + (bg_hover.green() - bg_base.green()) * self.hover_opacity)
        b = int(bg_base.blue() + (bg_hover.blue() - bg_base.blue()) * self.hover_opacity)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(r, g, b))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        
        border_base = QColor(colors["border-upload"])
        border_hover = QColor(colors["border-upload-hover"])
        br = int(border_base.red() + (border_hover.red() - border_base.red()) * self.hover_opacity)
        bg_g = int(border_base.green() + (border_hover.green() - border_base.green()) * self.hover_opacity)
        bb = int(border_base.blue() + (border_hover.blue() - border_base.blue()) * self.hover_opacity)
        
        pen = painter.pen()
        pen.setColor(QColor(br, bg_g, bb))
        pen.setWidth(2)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 12, 12)
        painter.end()

class UploadBox(QWidget):
    def __init__(self, on_file_selected, on_generate_clicked,
                 drop_title="Excel or CSV",
                 file_filter="Excel & CSV Files (*.xlsx *.xls *.csv)",
                 multi_file=False, instructions=None):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.on_generate_clicked = on_generate_clicked
        self.drop_title = drop_title
        self.file_filter = file_filter
        self.multi_file = multi_file
        self.instructions = instructions
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(28)
        
        # --- File selection area (Upper Dashed Box) ---
        self.drop_area = AnimatedDropArea()
        self.drop_area.setObjectName("UploadDropArea")
        self.drop_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.drop_area_layout = QVBoxLayout(self.drop_area)
        self.drop_area_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_area_layout.setSpacing(10)
        self.drop_area.mousePressEvent = self.open_file_dialog
        
        # File upload icon badge (manually paints circle and SVG)
        self.icon_badge = UploadIconBadge()
        self.drop_area_layout.addWidget(self.icon_badge, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.drop_title_label = QLabel(f"Drag & Drop your {self.drop_title} file here")
        self.drop_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_title_label.setObjectName("UploadDropTitle")
        self.drop_area_layout.addWidget(self.drop_title_label)
        
        self.drop_subtitle_label = QLabel("Or click to browse from your device")
        self.drop_subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_subtitle_label.setObjectName("UploadDropSubtitle")
        self.drop_area_layout.addWidget(self.drop_subtitle_label)
        
        self.layout.addWidget(self.drop_area, stretch=1)
        
        # --- Instructions Box (Separate Lower Box) ---
        if self.instructions and isinstance(self.instructions, dict):
            self.instructions_box = QFrame()
            self.instructions_box.setObjectName("InstructionsBox")
            self.instructions_layout = QVBoxLayout(self.instructions_box)
            self.instructions_layout.setContentsMargins(12, 12, 12, 12)
            
            # Header
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0, 0, 0, 0)
            
            icon_label = QLabel("ⓘ")
            icon_label.setObjectName("InstructionsIcon")
            
            header_label = QLabel(self.instructions.get("header", ""))
            header_label.setObjectName("InstructionsHeader")
            header_label.setWordWrap(True)
            
            header_layout.addWidget(icon_label)
            header_layout.addWidget(header_label, stretch=1)
            
            self.instructions_layout.addLayout(header_layout)
            
            # Bullets
            for bullet in self.instructions.get("bullets", []):
                bullet_label = QLabel(f"&bull; {bullet}")
                bullet_label.setObjectName("InstructionsBullet")
                bullet_label.setWordWrap(True)
                self.instructions_layout.addWidget(bullet_label)
                
            # Note
            note = self.instructions.get("note")
            if note:
                note_label = QLabel(note)
                note_label.setObjectName("InstructionsNote")
                note_label.setWordWrap(True)
                self.instructions_layout.addWidget(note_label)
            self.layout.addWidget(self.instructions_box)
        
        # --- Bottom Generate Plot Button (Green Bar) ---
        self.generate_btn = ActionButton("Generate Plot", style_type="primary", font_size=15, font_weight=700)
        self.generate_btn.setEnabled(False)
        self.generate_btn.setObjectName("UploadGenerateBtn")
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        self.layout.addWidget(self.generate_btn)
        
        self.current_file_path = None
        self.current_file_paths = []
        
    def reset(self):
        self.current_file_path = None
        self.current_file_paths = []
        self.drop_title_label.setText(f"Drag & Drop your {self.drop_title} file here")
        self.drop_title_label.setProperty("selected", False)
        self.drop_title_label.style().unpolish(self.drop_title_label)
        self.drop_title_label.style().polish(self.drop_title_label)
        self.drop_subtitle_label.show()
        self.generate_btn.setEnabled(False)
        
    def set_file(self, file_path):
        if isinstance(file_path, list):
            self.current_file_paths = file_path
            self.current_file_path = file_path[0] if file_path else None
        else:
            self.current_file_paths = [file_path] if file_path else []
            self.current_file_path = file_path
            
        if not self.current_file_paths:
            self.reset()
            return
            
        if len(self.current_file_paths) == 1:
            filename = os.path.basename(self.current_file_paths[0])
            self.drop_title_label.setText(f"Selected: <span style='font-weight: 700; color: {colors['text-accent']};'>{filename}</span>")
        else:
            self.drop_title_label.setText(f"Selected: <span style='font-weight: 700; color: {colors['text-accent']};'>{len(self.current_file_paths)} files</span>")
            
        self.drop_title_label.setProperty("selected", True)
        self.drop_title_label.style().unpolish(self.drop_title_label)
        self.drop_title_label.style().polish(self.drop_title_label)
        self.drop_subtitle_label.hide()
        
        self.generate_btn.setEnabled(True)
        
        if self.multi_file:
            self.on_file_selected(self.current_file_paths)
        else:
            self.on_file_selected(self.current_file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            if self.multi_file:
                file_paths = [url.toLocalFile() for url in urls]
                self.set_file(file_paths)
            else:
                file_path = urls[0].toLocalFile()
                self.set_file(file_path)
            
    def open_file_dialog(self, event=None):
        if self.multi_file:
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, "Open Data Files", "", self.file_filter
            )
            if file_paths:
                self.set_file(file_paths)
        else:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Data File", "", self.file_filter
            )
            if file_path:
                self.set_file(file_path)
