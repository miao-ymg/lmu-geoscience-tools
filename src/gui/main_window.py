import threading
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QLabel, QTreeWidget, QTreeWidgetItem, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from gui.components.loading_overlays import StartupOverlay

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
        self.showFullScreen()

        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Navbar
        navbar_widget = QWidget()
        navbar_widget.setObjectName("Navbar")
        navbar_widget.setFixedWidth(300)
        navbar_layout = QVBoxLayout(navbar_widget)
        navbar_layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title_label = QLabel("LMU Geoscience Tools")
        title_label.setObjectName("AppTitle")
        font = title_label.font()
        font.setPointSize(32)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setWordWrap(True)
        navbar_layout.addWidget(title_label)

        # Feature List (Tree Widget)
        self.feature_tree = QTreeWidget()
        self.feature_tree.setHeaderHidden(True)
        navbar_layout.addWidget(self.feature_tree)

        # Right Content Area
        self.content_area = QStackedWidget()
        self.content_area.setObjectName("ContentArea")

        # Add to main layout
        main_layout.addWidget(navbar_widget)
        main_layout.addWidget(self.content_area)

        self.setup_home_dashboard()

        # --- TOOLS ARE HERE ---
        self.features = {
            "QAPF Diagrams": "QAPF Diagrams",
            "TAS Diagrams": "TAS Diagrams",
            "Feldspar Diagrams": "Feldspar Diagrams"
        }

        self.setup_features()

        # Connect click event
        self.feature_tree.itemClicked.connect(self.on_feature_clicked)
        
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
        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.setContentsMargins(50, 50, 50, 50)
        
        home_layout.addStretch()
        
        # Dashboard Title
        welcome_label = QLabel("Welcome to LMU Geoscience Tools")
        welcome_label.setObjectName("DashboardTitle")
        font = welcome_label.font()
        font.setPointSize(36)
        font.setBold(True)
        welcome_label.setFont(font)
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(welcome_label)
        
        # Subtitle
        subtitle_label = QLabel("Select a tool from the sidebar to get started.")
        subtitle_label.setObjectName("DashboardSubtitle")
        font = subtitle_label.font()
        font.setPointSize(18)
        subtitle_label.setFont(font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(subtitle_label)
        
        home_layout.addStretch()
        
        # Add Home item to the tree
        home_item = QTreeWidgetItem(self.feature_tree)
        home_item.setText(0, "Home")
        
        self.content_area.addWidget(home_widget)
        home_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)
        
        # Select Home by default
        self.feature_tree.setCurrentItem(home_item)
        self.content_area.setCurrentIndex(0)

    def setup_features(self):
        for tool_name, content_text in self.features.items():
            tool_item = QTreeWidgetItem(self.feature_tree)
            tool_item.setText(0, tool_name)

            # Create a simple widget for this sub-feature
            content_widget = QWidget()
            content_layout = QVBoxLayout(content_widget)
            content_layout.setContentsMargins(0, 0, 0, 0)
            
            # Add title at the top left
            content_label = QLabel(content_text)
            content_label.setObjectName("FeatureTitle")
            font = content_label.font()
            font.setPointSize(26)
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
            else:
                # Add stretch to push content to top for unfinished tools
                content_layout.addStretch()
            
            self.content_area.addWidget(content_widget)
            
            # Store the index of the widget in the item
            tool_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)

    def on_feature_clicked(self, item, column):
        # Only switch content if it's a sub-feature (has UserRole data)
        index = item.data(0, Qt.ItemDataRole.UserRole)
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
