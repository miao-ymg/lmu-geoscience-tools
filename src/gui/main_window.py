import os
import sys
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QLabel, QTreeWidget, QTreeWidgetItem, QStackedWidget, QPushButton
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize, QByteArray, QVariantAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QColor

from gui.components.loading_overlays import StartupOverlay
from utils.i18n import i18n, tr

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class StartupWorker(QThread):
    progress = pyqtSignal(int, str)
    
    def run(self):
        try:
            self.progress.emit(10, "Loading data science libraries (pandas)...")
            import pandas
            self.progress.emit(35, "Loading visualization engine (matplotlib)...")
            import matplotlib.pyplot
            self.progress.emit(60, "Initializing QAPF module...")
            from tools.qapf.widget import QapfWidget
            self.progress.emit(80, "Initializing TAS module...")
            from tools.tas.widget import TasWidget
            self.progress.emit(90, "Initializing Feldspar module...")
            from tools.feldspar.widget import FeldsparWidget
            self.progress.emit(95, "Initializing Ultramafic module...")
            from tools.ultramafic.widget import UltramaficWidget
            self.progress.emit(98, "Initializing Raman Spectra module...")
            from tools.raman.widget import RamanWidget
            self.progress.emit(100, "Ready!")
            self.msleep(200) # Give a tiny pause at 100%
        except Exception as e:
            print(f"Error during background startup: {e}")

class LazyWidget(QWidget):
    def __init__(self, loader_fn):
        super().__init__()
        self.loader_fn = loader_fn
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.widget = None
        
    def load_widget(self):
        if self.widget is None:
            self.widget = self.loader_fn()
            self.layout.addWidget(self.widget)
        return self.widget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoPlottr")
        
        # Set minimum size close to screen resolution (e.g. 1280x800) and maximize/fullscreen
        self.setMinimumSize(1200, 750)
        self.showMaximized()

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Navbar
        navbar_widget = QWidget()
        navbar_widget.setObjectName("Navbar")
        navbar_widget.setFixedWidth(270)
        navbar_layout = QVBoxLayout(navbar_widget)
        navbar_layout.setContentsMargins(0, 0, 0, 20)
        navbar_layout.setSpacing(0)

        # Top Header Box
        header_container = QWidget()
        header_container.setObjectName("NavbarHeader")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(20, 24, 20, 16)
        header_layout.setSpacing(4)

        # Title
        self.app_title_label = QLabel("GeoPlottr")
        self.app_title_label.setObjectName("AppTitle")
        header_layout.addWidget(self.app_title_label)

        # Subtitle
        self.app_sub_label = QLabel("CHAIR OF GEOLOGY")
        self.app_sub_label.setObjectName("AppSubtitle")
        header_layout.addWidget(self.app_sub_label)

        navbar_layout.addWidget(header_container)

        # Section Header
        self.section_label = QLabel("GEOSCIENCE TOOLSET")
        self.section_label.setObjectName("SidebarSectionHeader")
        navbar_layout.addWidget(self.section_label)

        # Feature List (Tree Widget)
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderHidden(True)
        self.feature_tree.setRootIsDecorated(False)
        self.feature_tree.setIndentation(0)
        self.feature_tree.installEventFilter(self)
        navbar_layout.addWidget(self.feature_tree)

        # Language Switcher at bottom of Navbar
        from gui.components.language_bar import LanguageBar
        self.language_bar = LanguageBar()
        navbar_layout.addWidget(self.language_bar)

        # Right Content Area
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("ContentArea")

        # Add to main layout
        main_layout.addWidget(navbar_widget)
        main_layout.addWidget(self.content_area)

        self.setup_home_dashboard()

        # --- TOOLS ARE HERE ---
        self.TOOL_KEYS = [
            ("Feldspar Diagrams", "tool_feldspar"),
            ("QAPF Diagrams", "tool_qapf"),
            ("Raman Spectra", "tool_raman"),
            ("TAS Diagrams", "tool_tas"),
            ("Ultramafic Diagrams", "tool_ultramafic"),
        ]

        self.setup_features()

        # Connect i18n language updates
        i18n.language_changed.connect(self.retranslate_ui)
        self.retranslate_ui(i18n.get_language())

        # Sliding Highlight Widget for the sidebar
        from gui.components.sidebar_delegate import SidebarDelegate, SlidingAnimator
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QRect, QTimer
        
        self.sidebar_delegate = SidebarDelegate(self.feature_tree)
        self.feature_tree.setItemDelegate(self.sidebar_delegate)
        self.feature_tree.setMouseTracking(True)
        self.feature_tree.viewport().installEventFilter(self)
        
        self.sliding_animator = SlidingAnimator(self.feature_tree)
        self.sliding_animator.rectChanged.connect(lambda: self.sidebar_delegate.set_sliding_rect(self.sliding_animator.rect))
        
        self.highlight_anim = QPropertyAnimation(self.sliding_animator, b"rect")
        self.highlight_anim.setDuration(250)
        self.highlight_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self.highlight_anim.finished.connect(self.sidebar_delegate.unblock_hover)

        # Connect change event (supports both mouse and keyboard navigation)
        self.feature_tree.currentItemChanged.connect(self.on_feature_changed)
        
        # Setup the loading overlay
        self.startup_overlay = StartupOverlay(self.centralWidget())
        self.startup_overlay.show()
        
        # Disable interaction while loading
        self.centralWidget().setEnabled(False)
        
        self.startup_worker = StartupWorker()
        self.startup_worker.progress.connect(self.startup_overlay.update_progress)
        self.startup_worker.finished.connect(self.on_startup_finished)
        self.startup_worker.start()

        # Initialize highlight position once UI is laid out
        QTimer.singleShot(100, lambda: self.on_feature_changed(self.feature_tree.currentItem(), None))

    def on_startup_finished(self):
        self.startup_overlay.hide()
        self.startup_overlay.deleteLater()
        self.centralWidget().setEnabled(True)

    def setup_home_dashboard(self):
        class HomeDashboardWidget(QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setObjectName("HomeContainer")
                from PyQt6.QtGui import QPixmap
                bg_path = resource_path(os.path.join("resources", "home_bg.jpg"))
                self.bg_pixmap = QPixmap(bg_path) if os.path.exists(bg_path) else None

            def paintEvent(self, event):
                from PyQt6.QtGui import QPainter, QColor
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                # Fill base color
                painter.fillRect(self.rect(), QColor("#161B22"))
                
                if self.bg_pixmap and not self.bg_pixmap.isNull():
                    # Scale to cover the widget while keeping aspect ratio
                    scaled = self.bg_pixmap.scaled(
                        self.size(), 
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    # Center the pixmap
                    x = (self.width() - scaled.width()) // 2
                    y = (self.height() - scaled.height()) // 2
                    painter.drawPixmap(x, y, scaled)
                    
                painter.end()

        home_widget = HomeDashboardWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.setContentsMargins(60, 60, 60, 60)
        home_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        home_layout.addStretch(1)
        
        # Dashboard Title
        self.welcome_label = QLabel("Welcome to GeoPlottr")
        self.welcome_label.setObjectName("DashboardTitle")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(self.welcome_label)
        
        # Subtitle / Description text and guaranteed center alignment
        self.subtitle_label = QLabel(
            '<div style="text-align: center; line-height: 120%;">'
            'Select a tool from the sidebar to get started. These utilities facilitate rock classification,<br>'
            'mineral chemistry plotting, and spectral analysis for academic petrology labs.'
            '</div>'
        )
        self.subtitle_label.setObjectName("DashboardSubtitle")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        self.subtitle_label.setWordWrap(False)
        home_layout.addWidget(self.subtitle_label)
        
        home_layout.addStretch(1)
        
        # Bottom bar for Image credit at the right bottom
        credit_layout = QHBoxLayout()
        credit_layout.setContentsMargins(0, 0, 10, 5)
        credit_layout.addStretch()
        
        self.credit_label = QLabel(
            '<a href="https://www.magnific.com/free-ai-image/abstract-aerial-view-layered-geological-formations-desert-landscape_419049618.htm#fromView=keyword&page=1&position=2&uuid=9bdcd92b-9a15-4292-90c7-5f71638f2614&track=ais_hybrid&query=Geology+wallpaper" style="color: #627284; text-decoration: none; font-size: 11px;">Image by magnific</a>'
        )
        self.credit_label.setObjectName("HomeImageCredit")
        self.credit_label.setOpenExternalLinks(True)
        self.credit_label.setTextFormat(Qt.TextFormat.RichText)
        credit_layout.addWidget(self.credit_label)
        
        home_layout.addLayout(credit_layout)
        
        # Add Home Portal item to the tree
        self.home_item = QTreeWidgetItem(self.feature_tree)
        self.home_item.setText(0, "Home Portal")
        
        self.content_area.addWidget(home_widget)
        self.home_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)
        
        # Select Home Portal by default
        self.feature_tree.setCurrentItem(self.home_item)
        self.content_area.setCurrentIndex(0)

    def setup_features(self):
        self.tool_items = []
        self.feature_title_labels = []
        self.link_labels = []
        self.warning_link_labels = []

        # Create overlay popup layer for warning notes
        class WarningOverlay(QWidget):
            def __init__(self, tool_dir_name, parent=None):
                super().__init__(parent)
                self.tool_dir_name = tool_dir_name
                self.hide()

            def set_tool_title(self, title_text):
                self.title_label.setText(title_text)

            def load_content(self):
                # Clear existing items in scroll layout
                while self.content_layout.count():
                    item = self.content_layout.takeAt(0)
                    w = item.widget()
                    if w:
                        w.deleteLater()

                import yaml
                from utils.i18n import i18n
                lang = i18n.get_language()

                # Get path to warnings.yml
                if getattr(sys, 'frozen', False):
                    yml_path = os.path.join(sys._MEIPASS, 'tools', self.tool_dir_name, 'warnings.yml')
                else:
                    yml_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools', self.tool_dir_name, 'warnings.yml')

                bullets = []
                if os.path.exists(yml_path):
                    try:
                        with open(yml_path, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                            if isinstance(data, dict):
                                bullets = data.get(lang)
                                if not bullets:
                                    # Fallback if preferred language is empty/missing
                                    fallback_lang = 'de' if lang == 'en' else 'en'
                                    bullets = data.get(fallback_lang, []) or []
                    except Exception as e:
                        print(f"Error loading warnings.yml for {self.tool_dir_name}: {e}")

                if bullets:
                    for item in bullets:
                        # Check if item is a section header (e.g. starting with ⚠ or bold category)
                        is_header = item.startswith("⚠") or item.endswith(":")
                        lbl = QLabel(item if is_header else f"• {item}")
                        lbl.setWordWrap(True)
                        if is_header:
                            lbl.setStyleSheet("""
                                font-size: 21px;
                                font-weight: bold;
                                color: #ffb74d;
                                margin-top: 16px;
                                margin-bottom: 6px;
                                border: none;
                            """)
                        else:
                            lbl.setStyleSheet("""
                                font-size: 19px;
                                color: #c9d1d9;
                                line-height: 165%;
                                margin-bottom: 12px;
                                border: none;
                            """)
                        self.content_layout.addWidget(lbl)
                else:
                    empty_lbl = QLabel()
                    empty_lbl.setStyleSheet("font-size: 19px; color: #8b949e; italic; border: none;")
                    self.content_layout.addWidget(empty_lbl)

                self.content_layout.addStretch()

            def resizeEvent(self, event):
                if self.parent():
                    self.setGeometry(self.parent().rect())
                super().resizeEvent(event)

            def paintEvent(self, event):
                from PyQt6.QtGui import QPainter, QColor
                painter = QPainter(self)
                # Dimmed overlay background over the right view area
                painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
                painter.end()

        # Mapping tool names to folder names
        TOOL_DIR_MAP = {
            "Feldspar Diagrams": "feldspar",
            "QAPF Diagrams": "qapf",
            "Raman Spectra": "raman",
            "TAS Diagrams": "tas",
            "Ultramafic Diagrams": "ultramafic",
        }

        for tool_name, trans_key in self.TOOL_KEYS:
            tool_item = QTreeWidgetItem(self.feature_tree)
            tool_item.setText(0, tool_name)
            self.tool_items.append((tool_item, trans_key))

            # Create a simple widget for this sub-feature
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(40, 36, 40, 36)
            content_layout.setSpacing(28)
            
            from utils.urls import TOOL_URLS
            url = TOOL_URLS.get(tool_name, "")
            
            # Add title and link layout at the top left
            title_layout = QHBoxLayout()
            title_layout.setContentsMargins(0, 0, 0, 0)
            title_layout.setSpacing(32)
            
            title_label = QLabel(tool_name)
            title_label.setObjectName("FeatureTitle")
            font = title_label.font()
            font.setPointSize(36)
            font.setBold(True)
            title_label.setFont(font)
            
            title_layout.addWidget(title_label)
            self.feature_title_labels.append((title_label, trans_key))
            
            if url:
                class ClickableLinkLabel(QWidget):
                    def __init__(self, text, link, parent=None):
                        super().__init__(parent)
                        from main import resource_path
                        
                        self.link = link
                        self.setObjectName("FeatureLink")
                        self.setCursor(Qt.CursorShape.PointingHandCursor)
                        self.setToolTip(f"Open {link}")
                        
                        # Layout with 0 margins and 8px spacing
                        self.main_layout = QHBoxLayout(self)
                        self.main_layout.setContentsMargins(0, 0, 0, 0)
                        self.main_layout.setSpacing(8)
                        
                        self.text_label = QLabel(text)
                        self.text_label.setObjectName("FeatureLinkText")
                        
                        self.icon_label = QLabel()
                        self.icon_label.setObjectName("FeatureLinkIcon")
                        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        
                        # Prepare normal and hover colors
                        self.color_normal = QColor("#90c527")
                        self.color_hover = QColor("#9ef04d")
                        
                        # Load original SVG as template for color tinted pixmap
                        svg_path = resource_path("resources/icons/external-link.svg")
                        with open(svg_path, 'r', encoding='utf-8') as f:
                            self.svg_template = f.read()
                            
                        self.icon_label.setPixmap(self._render_icon_color(self.color_normal))
                        
                        self.main_layout.addWidget(self.text_label)
                        self.main_layout.addWidget(self.icon_label)
                        
                        # Animation: Color fade and subtle slide (shift margins)
                        self._anim_progress = 0.0
                        self.anim = QVariantAnimation(self)
                        self.anim.setDuration(260)
                        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
                        self.anim.valueChanged.connect(self._on_anim_frame)
                        
                    def _render_icon_color(self, color: QColor) -> QPixmap:
                        hex_code = color.name()
                        svg_str = self.svg_template.replace("#90C527", hex_code).replace("#90c527", hex_code)
                        pix = QPixmap()
                        pix.loadFromData(QByteArray(svg_str.encode('utf-8')), "SVG")
                        # Rendering via QIcon preserves macOS Retina High-DPI sharpness
                        return QIcon(pix).pixmap(16, 16)
                        
                    def _on_anim_frame(self, progress: float):
                        self._anim_progress = progress
                        
                        # Interpolate color between normal and hover
                        r = int(self.color_normal.red() + (self.color_hover.red() - self.color_normal.red()) * progress)
                        g = int(self.color_normal.green() + (self.color_hover.green() - self.color_normal.green()) * progress)
                        b = int(self.color_normal.blue() + (self.color_hover.blue() - self.color_normal.blue()) * progress)
                        current_color = QColor(r, g, b)
                        hex_code = current_color.name()
                        
                        # Update text label color
                        self.text_label.setStyleSheet(f"color: {hex_code};")
                        
                        # Update icon pixmap
                        self.icon_label.setPixmap(self._render_icon_color(current_color))
                        
                        # Subtle slide right: increase left margin from 0 to 6px
                        slide_px = int(round(progress * 6))
                        self.main_layout.setContentsMargins(slide_px, 0, 0, 0)
                        
                    def enterEvent(self, event):
                        self.anim.stop()
                        self.anim.setStartValue(self._anim_progress)
                        self.anim.setEndValue(1.0)
                        self.anim.start()
                        super().enterEvent(event)
                        
                    def leaveEvent(self, event):
                        self.anim.stop()
                        self.anim.setStartValue(self._anim_progress)
                        self.anim.setEndValue(0.0)
                        self.anim.start()
                        super().leaveEvent(event)
                        
                    def mousePressEvent(self, event):
                        if event.button() == Qt.MouseButton.LeftButton:
                            from PyQt6.QtGui import QDesktopServices
                            from PyQt6.QtCore import QUrl
                            QDesktopServices.openUrl(QUrl(self.link))
                        super().mousePressEvent(event)
                        
                link_label = ClickableLinkLabel("GEOWiki Page", url)
                title_layout.addWidget(link_label, alignment=Qt.AlignmentFlag.AlignBaseline)
                self.link_labels.append(link_label)

            title_layout.addStretch()

            # Warning Notes link (orange, aligned right in the same top HStack)
            class WarningLinkLabel(QWidget):
                def __init__(self, text, on_click_cb, parent=None):
                    super().__init__(parent)
                    self.on_click_cb = on_click_cb
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                    
                    layout = QHBoxLayout(self)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    self.text_label = QLabel(text)
                    self.text_label.setStyleSheet("color: #ff9800; font-weight: 600; text-decoration: underline;")
                    layout.addWidget(self.text_label)
                    
                def enterEvent(self, event):
                    self.text_label.setStyleSheet("color: #ffb74d; font-weight: 600; text-decoration: underline;")
                    super().enterEvent(event)
                    
                def leaveEvent(self, event):
                    self.text_label.setStyleSheet("color: #ff9800; font-weight: 600; text-decoration: underline;")
                    super().leaveEvent(event)
                    
                def mousePressEvent(self, event):
                    if event.button() == Qt.MouseButton.LeftButton:
                        self.on_click_cb()
                    super().mousePressEvent(event)

            # Warning Overlay Popup setup
            tool_dir_name = TOOL_DIR_MAP.get(tool_name, "")
            overlay = WarningOverlay(tool_dir_name, content_widget)
            overlay_layout = QVBoxLayout(overlay)
            overlay_layout.setContentsMargins(48, 48, 48, 48)
            
            from PyQt6.QtWidgets import QFrame, QScrollArea
            popup_card = QFrame()
            popup_card.setStyleSheet(
                "background-color: #161b22; border: 1px solid #30363d; border-radius: 12px;"
            )
            popup_layout = QVBoxLayout(popup_card)
            popup_layout.setContentsMargins(40, 36, 40, 40)
            popup_layout.setSpacing(32)
            
            popup_header = QHBoxLayout()
            overlay.title_label = QLabel()
            # Matching the app title font "IBM Plex Serif" / serif font
            overlay.title_label.setStyleSheet("""
                font-family: 'IBM Plex Serif', Georgia, 'Times New Roman', serif;
                font-size: 38px;
                font-weight: 600;
                color: #f0f6fc;
                border: none;
            """)
            popup_header.addWidget(overlay.title_label)
            popup_header.addStretch()
            
            close_btn = QPushButton("✕")
            close_btn.setFixedSize(42, 42)
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #8b949e;
                    font-size: 26px;
                    font-weight: bold;
                    border: none;
                    border-radius: 21px;
                }
                QPushButton:hover {
                    background-color: #21262d;
                    color: #f0f6fc;
                }
            """)
            close_btn.clicked.connect(overlay.hide)
            popup_header.addWidget(close_btn)
            
            popup_layout.addLayout(popup_header)

            # Scroll area for warnings content
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("""
                QScrollArea {
                    background: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background: #161b22;
                    width: 8px;
                    margin: 0px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background: #30363d;
                    min-height: 20px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #484f58;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                    height: 0px;
                }
            """)

            scroll_widget = QWidget()
            scroll_widget.setStyleSheet("background: transparent; border: none;")
            overlay.content_layout = QVBoxLayout(scroll_widget)
            overlay.content_layout.setContentsMargins(0, 0, 12, 0)
            overlay.content_layout.setSpacing(16)

            scroll_area.setWidget(scroll_widget)
            popup_layout.addWidget(scroll_area, stretch=1)
            
            overlay_layout.addWidget(popup_card)

            warning_link = WarningLinkLabel(
                tr("warning_notes"),
                lambda o=overlay, tk=trans_key: (
                    o.set_tool_title(tr("warning_notes_title", tool=tr(tk))),
                    o.load_content(),
                    o.setGeometry(o.parent().rect()),
                    o.raise_(),
                    o.show()
                )
            )
            title_layout.addWidget(warning_link, alignment=Qt.AlignmentFlag.AlignBaseline)
            self.warning_link_labels.append((warning_link, trans_key, overlay))

            content_layout.addLayout(title_layout)
            
            # Add the actual tool widget
            if tool_name == "QAPF Diagrams":
                def get_qapf():
                    from tools.qapf.widget import QapfWidget
                    return QapfWidget()
                tool_widget = LazyWidget(get_qapf)
                content_layout.addWidget(tool_widget, stretch=1)
            elif tool_name == "TAS Diagrams":
                def get_tas():
                    from tools.tas.widget import TasWidget
                    return TasWidget()
                tool_widget = LazyWidget(get_tas)
                content_layout.addWidget(tool_widget, stretch=1)
            elif tool_name == "Feldspar Diagrams":
                def get_feldspar():
                    from tools.feldspar.widget import FeldsparWidget
                    return FeldsparWidget()
                tool_widget = LazyWidget(get_feldspar)
                content_layout.addWidget(tool_widget, stretch=1)
            elif tool_name == "Ultramafic Diagrams":
                def get_ultramafic():
                    from tools.ultramafic.widget import UltramaficWidget
                    return UltramaficWidget()
                tool_widget = LazyWidget(get_ultramafic)
                content_layout.addWidget(tool_widget, stretch=1)
            elif tool_name == "Raman Spectra":
                def get_raman():
                    from tools.raman.widget import RamanWidget
                    return RamanWidget()
                tool_widget = LazyWidget(get_raman)
                content_layout.addWidget(tool_widget, stretch=1)
            else:
                # Add stretch to push content to top for unfinished tools
                content_layout.addStretch()
            
            self.content_area.addWidget(content_widget)
            
            # Store the index of the widget in the item
            tool_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)

    def retranslate_ui(self, lang=None):
        from utils.i18n import tr, i18n
        current_lang = i18n.get_language()

        # Header labels
        self.app_title_label.setText(tr("app_title"))
        self.app_sub_label.setText(tr("app_subtitle"))
        self.section_label.setText(tr("section_toolset"))
        
        # Home Dashboard
        if hasattr(self, 'home_item'):
            self.home_item.setText(0, tr("home_portal"))
        if hasattr(self, 'welcome_label'):
            self.welcome_label.setText(tr("home_welcome"))
        if hasattr(self, 'subtitle_label'):
            self.subtitle_label.setText(
                f'<div style="text-align: center; line-height: 120%;">{tr("home_description")}</div>'
            )
        if hasattr(self, 'credit_label'):
            self.credit_label.setText(
                f'<a href="https://www.magnific.com/free-ai-image/abstract-aerial-view-layered-geological-formations-desert-landscape_419049618.htm#fromView=keyword&page=1&position=2&uuid=9bdcd92b-9a15-4292-90c7-5f71638f2614&track=ais_hybrid&query=Geology+wallpaper" style="color: #627284; text-decoration: none; font-size: 11px;">{tr("home_image_credit")}</a>'
            )
            
        # Tool items in tree
        if hasattr(self, 'tool_items'):
            for item, trans_key in self.tool_items:
                item.setText(0, tr(trans_key))
                
        # Feature titles
        if hasattr(self, 'feature_title_labels'):
            for lbl, trans_key in self.feature_title_labels:
                lbl.setText(tr(trans_key))
                
        # Link labels
        if hasattr(self, 'link_labels'):
            for link_widget in self.link_labels:
                if hasattr(link_widget, 'text_label'):
                    link_widget.text_label.setText(tr("geowiki_page"))

        # Warning link labels
        if hasattr(self, 'warning_link_labels'):
            for link_widget, trans_key, overlay in self.warning_link_labels:
                if hasattr(link_widget, 'text_label'):
                    link_widget.text_label.setText(tr("warning_notes"))
                overlay.set_tool_title(tr("warning_notes_title", tool=tr(trans_key)))
                if overlay.isVisible():
                    overlay.load_content()
        
        # Trigger viewport redraw for custom item delegate
        if hasattr(self, 'feature_tree'):
            self.feature_tree.viewport().update()

    def on_feature_changed(self, current_item, previous_item):
        if not current_item:
            return
            
        # Check if this was triggered by a mouse click
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QRectF
        
        is_mouse_click = bool(QApplication.mouseButtons() & Qt.MouseButton.LeftButton)
        if is_mouse_click:
            self.sidebar_delegate.instant_white_row = self.feature_tree.indexOfTopLevelItem(current_item)
        else:
            self.sidebar_delegate.instant_white_row = -1
            
        # Update the sliding highlight animation
        target_rect = self.feature_tree.visualItemRect(current_item)
        if target_rect.isValid():
            target_rect = QRectF(14, target_rect.y() + 2, self.feature_tree.viewport().width() - 28, 42)
            
            if not self.sliding_animator.rect.isValid() or self.sliding_animator.rect.isEmpty():
                self.sliding_animator.rect = target_rect
            else:
                self.sidebar_delegate.hover_blocked = True
                self.sidebar_delegate.clear_hovers()
                self.highlight_anim.stop()
                self.highlight_anim.setStartValue(self.sliding_animator.rect)
                self.highlight_anim.setEndValue(target_rect)
                self.highlight_anim.start()
                
        # Only switch content if it's a sub-feature (has UserRole data)
        index = current_item.data(0, Qt.ItemDataRole.UserRole)
        if index is not None:
            widget = self.content_area.widget(index)
            # Find and load any LazyWidget inside this view
            for child in widget.findChildren(LazyWidget):
                child.load_widget()
            self.content_area.setCurrentIndex(index)

    def keyPressEvent(self, event):
        # Allow escaping fullscreen for testing
        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()

    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        # Block auto-repeat for up/down arrow keys in the feature tree
        if obj == self.feature_tree and event.type() == QEvent.Type.KeyPress:
            if event.isAutoRepeat() and event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                return True
                
        # Track hover in viewport
        if obj == self.feature_tree.viewport():
            if event.type() == QEvent.Type.MouseMove:
                item = self.feature_tree.itemAt(event.pos())
                for i in range(self.feature_tree.topLevelItemCount()):
                    t_item = self.feature_tree.topLevelItem(i)
                    self.sidebar_delegate.update_hover(i, t_item == item)
            elif event.type() == QEvent.Type.Leave:
                for i in range(self.feature_tree.topLevelItemCount()):
                    self.sidebar_delegate.update_hover(i, False)
                    
        return super().eventFilter(obj, event)
