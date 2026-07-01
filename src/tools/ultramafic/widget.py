import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QStackedWidget, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay

# Simple PlotView that just embeds the canvas
from PyQt6.QtWidgets import QHBoxLayout, QPushButton
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        self.canvas_layout = QVBoxLayout()
        self.layout.addLayout(self.canvas_layout, stretch=1)
        
        # Buttons
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
            QPushButton:hover { background-color: #c3f0c9; }
        """)
        self.download_btn.clicked.connect(on_download)
        btn_layout.addWidget(self.download_btn)
        
        self.new_sample_btn = QPushButton("New sample")
        self.new_sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #333333;
                color: #e0e0e0;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { background-color: #444444; }
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

import pandas as pd
from tools.ultramafic.data import extract_and_normalize
from tools.ultramafic.plot import plot_ultramafic

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)

    def __init__(self, file_path=None, normalized_df=None):
        super().__init__()
        self.file_path = file_path
        self.normalized_df = normalized_df

    def run(self):
        try:
            if self.file_path:
                df = pd.read_excel(self.file_path)
                self.normalized_df = extract_and_normalize(df)
            
            fig = plot_ultramafic(self.normalized_df, dark_mode=True)
            self.finished.emit(fig, "", self.normalized_df)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.finished.emit(None, str(e), None)


class UltramaficWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked)
        self.plot_view = PlotView(self.show_upload, self.download_plot)
        self.loading_overlay = PanelOverlay()

        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        layout.addWidget(self.stack)

        self.current_file_path = None
        self.normalized_df = None
        
        self.worker = None

    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)

    def on_file_selected(self, file_path):
        self.current_file_path = file_path

    def on_generate_clicked(self):
        if not self.current_file_path:
            return
        self.start_worker(file_path=self.current_file_path, show_loading=True)

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        self.start_worker(normalized_df=self.normalized_df, show_loading=False)
            
    def start_worker(self, file_path=None, normalized_df=None, show_loading=True):
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(file_path, normalized_df)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, normalized_df):
        self.worker = None
        
        if error_msg:
            QMessageBox.critical(self, "Error", error_msg)
            self.stack.setCurrentIndex(0)
            return
            
        if normalized_df is not None:
            self.normalized_df = normalized_df
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        from PyQt6.QtWidgets import QFileDialog
        
        if not self.plot_view.current_fig:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            os.path.expanduser("~/Desktop/ultramafic_diagram.png"),
            "PNG Images (*.png);;PDF Documents (*.pdf);;SVG Graphics (*.svg)"
        )
        
        if file_path:
            try:
                # Generate a light-mode version for the exported file
                fig = plot_ultramafic(self.normalized_df, dark_mode=False)
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", f"Plot successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save plot:\n{str(e)}")
