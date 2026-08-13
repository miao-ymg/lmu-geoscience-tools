import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QMessageBox, QStackedWidget, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView
from .data import extract_and_normalize
from .plot import plot_ultramafic

class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download):
        super().__init__(on_new_sample)
        self.download_btn.clicked.connect(on_download)

import pandas as pd
from tools.ultramafic.data import extract_and_normalize
from tools.ultramafic.plot import plot_ultramafic

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)

    def __init__(self, normalized_df):
        super().__init__()
        self.normalized_df = normalized_df

    def run(self):
        try:
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
        instructions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'column_aliases.yml')
        from utils.instructions import generate_yaml_instructions
        instructions = generate_yaml_instructions(instructions_path)
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked, instructions=instructions)
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
            
        try:
            df = pd.read_excel(self.current_file_path)
            normalized_df = extract_and_normalize(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return
            
        self.start_worker(normalized_df=normalized_df, show_loading=True)

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        self.start_worker(normalized_df=self.normalized_df, show_loading=False)
            
    def start_worker(self, normalized_df, show_loading=True):
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(normalized_df)
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
        self.plot_view.handle_download(
            self,
            lambda: plot_ultramafic(self.normalized_df, dark_mode=False),
            "ultramafic_diagram.png"
        )
