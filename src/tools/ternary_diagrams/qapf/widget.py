import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, 
    QStackedWidget, QMessageBox, QHBoxLayout, QButtonGroup
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from .data import load_and_validate_data, normalize_qapf
from .plot import plot_qapf

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

class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download, on_highlight_changed):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Highlight controls
        highlight_layout = QVBoxLayout()
        
        highlight_label = QLabel("Highlight Axis:")
        highlight_label.setStyleSheet("color: #e0e0e0; font-weight: bold; font-size: 14px; margin-bottom: 5px;")
        highlight_layout.addWidget(highlight_label)
        
        buttons_layout = QHBoxLayout()
        self.highlight_group = QButtonGroup(self)
        
        for val in ['None', 'Q', 'A', 'P', 'F']:
            btn = QPushButton(val)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #333333;
                    color: #e0e0e0;
                    border-radius: 5px;
                    padding: 8px 15px;
                    font-size: 14px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:checked {
                    background-color: #a6e3a1;
                    color: #1e1e1e;
                }
                QPushButton:hover:!checked {
                    background-color: #444444;
                }
            """)
            if val == 'None':
                btn.setChecked(True)
            self.highlight_group.addButton(btn)
            buttons_layout.addWidget(btn)
            
        buttons_layout.addStretch()
        highlight_layout.addLayout(buttons_layout)
        
        self.layout.addLayout(highlight_layout)
        
        self.highlight_group.buttonClicked.connect(lambda btn: on_highlight_changed(btn.text()))
        
        self.canvas_layout = QVBoxLayout()
        self.layout.addLayout(self.canvas_layout, stretch=1)
        
        btn_layout = QHBoxLayout()
        
        self.download_btn = QPushButton("Download Image")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #a6e3a1;
                color: #1e1e1e;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c3f0c9;
            }
        """)
        self.download_btn.clicked.connect(on_download)
        btn_layout.addWidget(self.download_btn)
        
        self.new_sample_btn = QPushButton("New sample")
        # Change new sample button to the generic neutral button style
        self.new_sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
        """)
        self.new_sample_btn.clicked.connect(on_new_sample)
        btn_layout.addWidget(self.new_sample_btn)
        
        self.layout.addLayout(btn_layout)
        self.current_fig = None
        self.canvas = None
        
    def set_plot(self, fig):
        self.current_fig = fig
        for i in reversed(range(self.canvas_layout.count())): 
            widget = self.canvas_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
            
        self.canvas = FigureCanvas(fig)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas_layout.addWidget(self.canvas)

class QapfWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked)
        self.plot_view = PlotView(self.show_upload, self.download_plot, self.on_highlight_changed)
        
        self.stack.addWidget(self.upload_view)
        self.stack.addWidget(self.plot_view)
        
        layout.addWidget(self.stack)
        
        self.current_file_path = None
        self.normalized_df = None
        self.current_highlight = 'None'
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_path):
        self.current_file_path = file_path
        
    def on_highlight_changed(self, highlight_val):
        self.current_highlight = highlight_val if highlight_val != 'None' else None
        self.refresh_plot()
        
    def on_generate_clicked(self):
        if not self.current_file_path:
            return
            
        df, error = load_and_validate_data(self.current_file_path)
        
        if error:
            QMessageBox.warning(self, "Data Error", error)
            return
            
        try:
            self.normalized_df = normalize_qapf(df)
            self.refresh_plot()
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", f"An error occurred while generating the plot: {str(e)}")

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        try:
            fig = plot_qapf(self.normalized_df, dark_mode=True, highlight_axis=self.current_highlight)
            self.plot_view.set_plot(fig)
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", f"An error occurred while regenerating the plot: {str(e)}")

    def download_plot(self):
        if self.normalized_df is None or not self.current_file_path:
            return
            
        filename = os.path.basename(self.current_file_path)
        base_name, _ = os.path.splitext(filename)
        
        suffix = ""
        if self.current_highlight and self.current_highlight != 'None':
            suffix = f"_{self.current_highlight}"
            
        default_save_name = f"{base_name}_plot{suffix}.png"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", default_save_name, "PNG Images (*.png);;PDF Files (*.pdf)"
        )
        if file_path:
            try:
                # Generate light-theme plot for saving
                fig_to_save = plot_qapf(self.normalized_df, dark_mode=False, highlight_axis=self.current_highlight)
                fig_to_save.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", "Plot successfully saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the plot: {str(e)}")
