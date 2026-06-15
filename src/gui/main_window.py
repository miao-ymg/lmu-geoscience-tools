from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QLabel, QTreeWidget, QTreeWidgetItem, QStackedWidget)
from PyQt6.QtCore import Qt

from tools.ternary_diagrams.qapf.widget import QapfWidget

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

        # --- TOOLS ARE HERE ---
        self.features = {
            "Ternary Diagrams": {
                "QAPF": "QAPF Diagrams",
                "Feldspars": "Feldspar Diagrams"
            }
        }

        self.setup_features()

        # Connect click event
        self.feature_tree.itemClicked.connect(self.on_feature_clicked)

    def setup_features(self):
        for group_name, sub_features in self.features.items():
            group_item = QTreeWidgetItem(self.feature_tree)
            group_item.setText(0, group_name)
            group_item.setExpanded(True)

            for sub_name, content_text in sub_features.items():
                sub_item = QTreeWidgetItem(group_item)
                sub_item.setText(0, sub_name)
                
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
                if sub_name == "QAPF":
                    tool_widget = QapfWidget()
                    content_layout.addWidget(tool_widget, stretch=1)
                else:
                    # Add stretch to push content to top for unfinished tools
                    content_layout.addStretch()
                
                self.content_area.addWidget(content_widget)
                
                # Store the index of the widget in the item
                sub_item.setData(0, Qt.ItemDataRole.UserRole, self.content_area.count() - 1)

    def on_feature_clicked(self, item, column):
        # Only switch content if it's a sub-feature (has UserRole data)
        index = item.data(0, Qt.ItemDataRole.UserRole)
        if index is not None:
            self.content_area.setCurrentIndex(index)

    def keyPressEvent(self, event):
        # Allow escaping fullscreen for testing
        if event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()
