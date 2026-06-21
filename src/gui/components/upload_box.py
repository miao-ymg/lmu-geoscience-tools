import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class UploadBox(QWidget):
    def __init__(self, on_file_selected, on_generate_clicked):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.on_generate_clicked = on_generate_clicked
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        
        # --- File selection area ---
        self.drop_label = QLabel("Drag & Drop your Excel or CSV file here\nor click to browse")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setTextFormat(Qt.TextFormat.RichText)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaaaaa;
                border-radius: 10px;
                background-color: #252526;
                font-size: 18px;
                color: #e0e0e0;
                padding: 50px;
            }
        """)
        self.drop_label.mousePressEvent = self.open_file_dialog
        self.layout.addWidget(self.drop_label, stretch=1)
        
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.upload_btn.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.upload_btn)
        
        self.generate_btn = QPushButton("Generate Plot")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e1e;
                font-size: 18px;
                font-weight: bold;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:disabled {
                background-color: #444444;
                color: #888888;
            }
            QPushButton:hover:!disabled {
                background-color: #c3f0c9;
            }
        """)
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        self.layout.addWidget(self.generate_btn)
        
        self.current_file_path = None
        
    def reset(self):
        self.current_file_path = None
        self.drop_label.setText("Drag & Drop your Excel or CSV file here\nor click to browse")
        self.generate_btn.setEnabled(False)
        
    def set_file(self, file_path):
        self.current_file_path = file_path
        filename = os.path.basename(file_path)
        
        # Show selected filename inside the drag area with bold green accent
        self.drop_label.setText(
            f"Selected: <span style='color: #a6e3a1; font-weight: bold;'>{filename}</span>"
            f"<br><br><span style='font-size: 14px; color: #aaaaaa;'>(Drag & Drop another file to change)</span>"
        )
        self.generate_btn.setEnabled(True)
        self.on_file_selected(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.set_file(file_path)
            
    def open_file_dialog(self, event=None):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Data File", "", "Excel & CSV Files (*.xlsx *.xls *.csv)"
        )
        if file_path:
            self.set_file(file_path)
