import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

class UploadBox(QWidget):
    def __init__(self, on_file_selected, on_generate_clicked,
                 drop_text="Drag & Drop your Excel or CSV file here\nor click to browse",
                 file_filter="Excel & CSV Files (*.xlsx *.xls *.csv)",
                 multi_file=False):
        super().__init__()
        self.on_file_selected = on_file_selected
        self.on_generate_clicked = on_generate_clicked
        self.drop_text = drop_text
        self.file_filter = file_filter
        self.multi_file = multi_file
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
        self.current_file_paths = []
        
    def reset(self):
        self.current_file_path = None
        self.current_file_paths = []
        self.drop_label.setText(self.drop_text)
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
            label_text = f"Selected: <span style='color: #a6e3a1; font-weight: bold;'>{filename}</span>"
        else:
            label_text = f"Selected: <span style='color: #a6e3a1; font-weight: bold;'>{len(self.current_file_paths)} files</span>"
            
        # Show selected filename inside the drag area with bold green accent
        self.drop_label.setText(
            f"{label_text}"
            f"<br><br><span style='font-size: 14px; color: #aaaaaa;'>(Drag & Drop again to change)</span>"
        )
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
