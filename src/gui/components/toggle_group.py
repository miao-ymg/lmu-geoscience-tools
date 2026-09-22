from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QButtonGroup
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QVariantAnimation
from theme import colors, hex_to_rgb

class ToggleGroup(QWidget):
    selectionChanged = pyqtSignal(str)
    
    def __init__(self, label_text, options, default_option=None, label_key=None, option_keys=None):
        super().__init__()
        self.label_text = label_text
        self.label_key = label_key
        self.option_keys = option_keys or {}  # mapping: internal_key -> translation_key
        self.options = options
        self.current_selection = default_option
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(6)
        
        # Label
        self.label = QLabel(label_text.rstrip(':'))
        self.label.setObjectName("ToggleGroupLabel")
        self.layout.addWidget(self.label)
        
        # Buttons layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(8)
        self.button_group = QButtonGroup(self)
        
        self.update_options(options, default_option)
        
        self.buttons_layout.addStretch()
        self.layout.addLayout(self.buttons_layout)
        
        from utils.i18n import i18n
        self.retranslate_ui()
        i18n.language_changed.connect(self.retranslate_ui)
        
    def retranslate_ui(self, lang=None):
        from utils.i18n import tr
        if self.label_key:
            translated_title = tr(self.label_key).rstrip(':')
            self.label.setText(translated_title)
        
        # Update text on each button while keeping their internal key
        for btn in self.button_group.buttons():
            key = getattr(btn, 'internal_key', btn.text())
            trans_key = self.option_keys.get(key)
            if trans_key:
                btn.setText(tr(trans_key))
            else:
                btn.setText(key)
            if isinstance(btn, FadingButton):
                btn.update_style()
                
    def get_selected(self):
        return self.current_selection

    def set_selected(self, key):
        self.current_selection = key
        for btn in self.button_group.buttons():
            b_key = getattr(btn, 'internal_key', btn.text())
            if b_key == key:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
            if isinstance(btn, FadingButton):
                btn.update_style()

    def update_options(self, options, default_option=None, option_keys=None):
        if option_keys is not None:
            self.option_keys = option_keys
            
        # Remove old buttons
        for btn in self.button_group.buttons():
            self.button_group.removeButton(btn)
            self.buttons_layout.removeWidget(btn)
            btn.deleteLater()
            
        self.options = options
        if default_option is not None:
            self.current_selection = default_option
            
        from utils.i18n import tr
        for val in options:
            trans_key = self.option_keys.get(val)
            display_text = tr(trans_key) if trans_key else val
            btn = FadingButton(display_text)
            btn.internal_key = val
            
            if val == self.current_selection:
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
        self.button_group.buttonClicked.connect(self._on_button_clicked)
        
    def _on_button_clicked(self, btn):
        for b in self.button_group.buttons():
            if isinstance(b, FadingButton):
                b.update_style()
        internal_key = getattr(btn, 'internal_key', btn.text())
        self.current_selection = internal_key
        self.selectionChanged.emit(internal_key)

class FadingButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setObjectName("ToggleBtn")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        
        self.anim = QVariantAnimation(self)
        self.anim.setDuration(150)
        self.anim.valueChanged.connect(self._on_anim_value)
        self.current_hover = 0.0
        
        self.check_anim = QVariantAnimation(self)
        self.check_anim.setDuration(150)
        self.check_anim.valueChanged.connect(self._on_check_anim_value)
        self.current_checked = 1.0 if self.isChecked() else 0.0
        
        self.toggled.connect(self._on_toggled)
        self.update_style()
        
    def enterEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.current_hover)
        self.anim.setEndValue(1.0)
        self.anim.start()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.anim.stop()
        self.anim.setStartValue(self.current_hover)
        self.anim.setEndValue(0.0)
        self.anim.start()
        super().leaveEvent(event)
        
    def _on_anim_value(self, val):
        self.current_hover = val
        self.update_style()
        
    def _on_check_anim_value(self, val):
        self.current_checked = val
        self.update_style()
        
    def _on_toggled(self, checked):
        self.check_anim.stop()
        self.check_anim.setStartValue(self.current_checked)
        self.check_anim.setEndValue(1.0 if checked else 0.0)
        self.check_anim.start()
            
    def update_style(self):
        base_bg = hex_to_rgb(colors["anim-toggle-base-bg"])
        hover_bg = hex_to_rgb(colors["anim-toggle-hover-bg"])
        
        # Base colors (unhovered to hovered)
        r_base = base_bg[0] + (hover_bg[0] - base_bg[0]) * self.current_hover
        g_base = base_bg[1] + (hover_bg[1] - base_bg[1]) * self.current_hover
        b_base = base_bg[2] + (hover_bg[2] - base_bg[2]) * self.current_hover
        
        # Border base: match background to appear borderless
        br_base, bg_base, bb_base = r_base, g_base, b_base
        
        # Text base (unhovered to hovered)
        base_txt = hex_to_rgb(colors["anim-toggle-base-text"])
        hover_txt = hex_to_rgb(colors["anim-toggle-hover-text"])
        tr_base = base_txt[0] + (hover_txt[0] - base_txt[0]) * self.current_hover
        tg_base = base_txt[1] + (hover_txt[1] - base_txt[1]) * self.current_hover
        tb_base = base_txt[2] + (hover_txt[2] - base_txt[2]) * self.current_hover
        
        # Checked colors
        r_chk, g_chk, b_chk = hex_to_rgb(colors["anim-toggle-checked-bg"])
        br_chk, bg_chk, bb_chk = hex_to_rgb(colors["anim-toggle-checked-border"])
        tr_chk, tg_chk, tb_chk = hex_to_rgb(colors["anim-toggle-checked-text"])
        
        # Final interpolation
        r = int(r_base + (r_chk - r_base) * self.current_checked)
        g = int(g_base + (g_chk - g_base) * self.current_checked)
        b = int(b_base + (b_chk - b_base) * self.current_checked)
        
        br = int(br_base + (br_chk - br_base) * self.current_checked)
        bg = int(bg_base + (bg_chk - bg_base) * self.current_checked)
        bb = int(bb_base + (bb_chk - bb_base) * self.current_checked)
        
        tr = int(tr_base + (tr_chk - tr_base) * self.current_checked)
        tg = int(tg_base + (tg_chk - tg_base) * self.current_checked)
        tb = int(tb_base + (tb_chk - tb_base) * self.current_checked)
        
        self.setStyleSheet(f"QPushButton#ToggleBtn {{ background-color: rgb({r}, {g}, {b}); color: rgb({tr}, {tg}, {tb}); border: 1px solid rgb({br}, {bg}, {bb}); margin: 0px; padding: 0px 16px; border-radius: 6px; font-weight: 600; font-size: 15px; }}")

