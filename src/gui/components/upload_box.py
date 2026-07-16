import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class UploadBox(QWidget):
    def __init__(self, on_file_selected, on_generate_clicked,
                 drop_text="Drag & Drop your Excel or CSV file here\nor click to browse",
                 file_filter="Excel & CSV Files (*.xlsx *.xls *.csv)"):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.on_generate_clicked = on_generate_clicked
        self.drop_text = drop_text
        self.file_filter = file_filter
        self.setAcceptDrops(True)
        
        self.layout = QVBoxLayout(self)
        
        # --- File selection area ---
        self.drop_label = QLabel(self.drop_text)
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_label.setTextFormat(Qt.TextFormat.RichText)
        self.drop_label.setObjectName("UploadDropLabel")
        self.drop_label.mousePressEvent = self.open_file_dialog
        self.layout.addWidget(self.drop_label, stretch=1)
        
        self.upload_btn = QPushButton("Upload File")
        self.upload_btn.setObjectName("UploadSelectBtn")
        self.upload_btn.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.upload_btn)
        
        self.generate_btn = QPushButton("Generate Plot")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setObjectName("UploadGenerateBtn")
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        self.layout.addWidget(self.generate_btn)
        
        self.current_file_path = None
        
    def reset(self):
        self.current_file_path = None
        self.drop_label.setText(self.drop_text)
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
            self, "Open Data File", "", self.file_filter
        )
        if file_path:
            self.set_file(file_path)
