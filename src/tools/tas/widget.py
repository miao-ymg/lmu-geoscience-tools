import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, 
    QStackedWidget, QMessageBox, QHBoxLayout
)
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from gui.components.upload_box import UploadBox
from gui.components.toggle_group import ToggleGroup
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView
from .data import load_and_validate_data, normalize_tas
from .plot import plot_tas

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)  # fig, error_msg, normalized_df
    
    def __init__(self, normalized_df, classification):
        super().__init__()
        self.normalized_df = normalized_df
        self.classification = classification
        
    def run(self):
        error_msg = None
        fig = None
        try:
            if self.normalized_df is not None:
                fig = plot_tas(self.normalized_df, dark_mode=True, rock_type=self.classification)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.normalized_df)

class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download, on_classification_changed):
        super().__init__(on_new_sample)
        
        self.classification_toggle = ToggleGroup("Classification:", ['Volcanites', 'Plutonites'], 'Volcanites')
        self.classification_toggle.selectionChanged.connect(on_classification_changed)
        
        self.add_top_widget(self.classification_toggle)
        self.add_top_stretch()
        
        self.download_btn.clicked.connect(on_download)


class TasWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked)
        self.plot_view = PlotView(self.show_upload, self.download_plot, self.on_classification_changed)
        self.loading_overlay = PanelOverlay()
        
        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        
        layout.addWidget(self.stack)
        
        self.current_file_path = None
        self.normalized_df = None
        self.current_classification = 'Volcanites'
        
        self.worker = None
        self.old_workers = []
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_path):
        self.current_file_path = file_path
        
    def on_classification_changed(self, classification_val):
        self.current_classification = classification_val
        self.refresh_plot()
        
    def on_generate_clicked(self):
        if not self.current_file_path:
            return
            
        try:
            df, error = load_and_validate_data(self.current_file_path)
            if error:
                QMessageBox.critical(self, "Error", error)
                return
            normalized_df = normalize_tas(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return
            
        self.start_worker(normalized_df=normalized_df, show_loading=True)

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        self.start_worker(normalized_df=self.normalized_df, show_loading=False)
            
    def start_worker(self, normalized_df, show_loading=True):
        if self.worker is not None and self.worker.isRunning():
            self.old_workers.append(self.worker)
            
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(normalized_df, self.current_classification)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, normalized_df):
        sender = self.sender()
        if sender != self.worker:
            if hasattr(self, 'old_workers') and sender in self.old_workers:
                sender.deleteLater()
                self.old_workers.remove(sender)
            return
            
        self.worker = None
        
        if error_msg:
            self.stack.setCurrentIndex(0)
            QMessageBox.critical(self, "Error", error_msg)
            return
            
        if normalized_df is not None:
            self.normalized_df = normalized_df
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_tas(self.normalized_df, dark_mode=False, rock_type=self.current_classification),
            "tas_diagram.png"
        )
