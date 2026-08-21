import os
import sys
import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QLabel, QTreeWidget, QTreeWidgetItem, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gui.components.loading_overlays import StartupOverlay

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
        self.setWindowTitle("LMU Geoscience Tools")
        
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
        title_label = QLabel("LMU Geoscience Tools")
        title_label.setObjectName("AppTitle")
        header_layout.addWidget(title_label)

        # Subtitle
        sub_label = QLabel("CHAIR OF GEOLOGY")
        sub_label.setObjectName("AppSubtitle")
        header_layout.addWidget(sub_label)

        navbar_layout.addWidget(header_container)

        # Section Header
        section_label = QLabel("GEOSCIENCE TOOLSET")
        section_label.setObjectName("SidebarSectionHeader")
        navbar_layout.addWidget(section_label)

        # Feature List (Tree Widget)
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderHidden(True)
        self.feature_tree.setRootIsDecorated(False)
        self.feature_tree.setIndentation(0)
        self.feature_tree.installEventFilter(self)
        navbar_layout.addWidget(self.feature_tree)

        # Right Content Area
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("ContentArea")

        # Add to main layout
        main_layout.addWidget(navbar_widget)
        main_layout.addWidget(self.content_area)

        self.setup_home_dashboard()

        # --- TOOLS ARE HERE ---
        features = {
            "QAPF Diagrams": "QAPF Diagrams",
            "TAS Diagrams": "TAS Diagrams",
            "Feldspar Diagrams": "Feldspar Diagrams",
            "Ultramafic Diagrams": "Ultramafic Diagrams",
            "Raman Spectra": "Raman Spectra"
        }
        self.features = {k: features[k] for k in sorted(features.keys())}

        self.setup_features()

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
        welcome_label = QLabel("Welcome to LMU Geoscience Tools")
        welcome_label.setObjectName("DashboardTitle")
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(welcome_label)
        
        # Subtitle / Description text and guaranteed center alignment
        subtitle_label = QLabel(
            '<div style="text-align: center; line-height: 120%;">'
            'Select a tool from the sidebar to get started. These utilities facilitate rock classification,<br>'
            'mineral chemistry plotting, and spectral analysis for academic petrology labs.'
            '</div>'
        )
        subtitle_label.setObjectName("DashboardSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        subtitle_label.setWordWrap(False)
        home_layout.addWidget(subtitle_label)
        
        home_layout.addStretch(1)
        
        # Bottom bar for Image credit at the right bottom
        credit_layout = QHBoxLayout()
        credit_layout.setContentsMargins(0, 0, 10, 5)
        credit_layout.addStretch()
        
        credit_label = QLabel(
            '<a href="https://www.magnific.com/free-ai-image/abstract-aerial-view-layered-geological-formations-desert-landscape_419049618.htm#fromView=keyword&page=1&position=2&uuid=9bdcd92b-9a15-4292-90c7-5f71638f2614&track=ais_hybrid&query=Geology+wallpaper" style="color: #627284; text-decoration: none; font-size: 11px;">Image by magnific</a>'
        )
        credit_label.setObjectName("HomeImageCredit")
        credit_label.setOpenExternalLinks(True)
        credit_label.setTextFormat(Qt.TextFormat.RichText)
        credit_layout.addWidget(credit_label)
        
        home_layout.addLayout(credit_layout)
        
        # Add Home Portal item to the tree
        home_item = QTreeWidgetItem(self.feature_tree)
        home_item.setText(0, "Home Portal")
        
        self.content_area.addWidget(home_widget)
        home_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)
        
        # Select Home Portal by default
        self.feature_tree.setCurrentItem(home_item)
        self.content_area.setCurrentIndex(0)

    def setup_features(self):
        for tool_name, content_text in self.features.items():
            tool_item = QTreeWidgetItem(self.feature_tree)
            tool_item.setText(0, tool_name)

            # Create a simple widget for this sub-feature
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(40, 36, 40, 36)
            content_layout.setSpacing(28)
            
            # Add title at the top left
            content_label = QLabel(content_text)
            content_label.setObjectName("FeatureTitle")
            font = content_label.font()
            font.setPointSize(36)
            font.setBold(True)
            content_label.setFont(font)
            content_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            content_layout.addWidget(content_label)
            
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

    def on_feature_changed(self, current_item, previous_item):
        if not current_item:
            return
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
        return super().eventFilter(obj, event)
