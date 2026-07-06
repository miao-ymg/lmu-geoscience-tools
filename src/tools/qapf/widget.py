import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, 
    QStackedWidget, QMessageBox, QHBoxLayout, QButtonGroup
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from .data import load_and_validate_data, normalize_qapf
from .plot import plot_qapf
from gui.components.toggle_group import ToggleGroup
from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object, str)  # fig, error_msg, normalized_df, mode
    
    def __init__(self, normalized_df, mode, highlight, classification):
        super().__init__()
        self.normalized_df = normalized_df
        self.mode = mode
        self.highlight = highlight
        self.classification = classification
        
    def run(self):
        error_msg = None
        fig = None
        try:
            if self.normalized_df is not None:
                fig = plot_qapf(self.normalized_df, mode=self.mode, dark_mode=True, 
                                highlight_axis=self.highlight, classification=self.classification)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.normalized_df, self.mode)

class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download, on_highlight_changed, on_classification_changed):
        super().__init__(on_new_sample)
        
        self.highlight_toggle = ToggleGroup("Highlight Axis:", ['None', 'A', 'P'], 'None')
        self.classification_toggle = ToggleGroup("Classification:", ['None', 'Volcanites', 'Plutonites'], 'None')
        
        self.highlight_toggle.selectionChanged.connect(on_highlight_changed)
        self.classification_toggle.selectionChanged.connect(on_classification_changed)
        
        self.add_top_widget(self.highlight_toggle)
        self.add_top_widget(self.classification_toggle)
        self.add_top_stretch()
        
        self.download_btn.clicked.connect(on_download)
        
        self.update_highlight_options('QAPF')
        
    def update_highlight_options(self, mode):
        options = ['None', 'A', 'P']
        if mode in ['QAPF', 'QAP']:
            options.insert(1, 'Q')
        if mode in ['QAPF', 'APF']:
            options.append('F')
        self.highlight_toggle.update_options(options, 'None')

class QapfWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked)
        self.plot_view = PlotView(self.show_upload, self.download_plot, self.on_highlight_changed, self.on_classification_changed)
        self.loading_overlay = PanelOverlay()
        
        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        
        layout.addWidget(self.stack)
        
        self.current_file_path = None
        self.normalized_df = None
        self.current_highlight = 'None'
        self.current_classification = 'None'
        self.current_mode = 'QAPF'
        
        self.worker = None
        self.old_workers = []
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_path):
        self.current_file_path = file_path
        
    def on_highlight_changed(self, highlight_val):
        self.current_highlight = highlight_val if highlight_val != 'None' else None
        self.refresh_plot()
        
    def on_classification_changed(self, classification_val):
        self.current_classification = classification_val if classification_val != 'None' else None
        self.refresh_plot()
        
    def on_generate_clicked(self):
        if not self.current_file_path:
            return
            
        try:
            df, mode, error = load_and_validate_data(self.current_file_path)
            if error:
                QMessageBox.critical(self, "Error", error)
                return
            normalized_df = normalize_qapf(df)
            
            if self.current_mode != mode:
                self.current_mode = mode
                self.current_highlight = 'None'
                self.current_classification = 'None'
                self.plot_view.update_highlight_options(mode)
                self.plot_view.classification_toggle.update_options(['None', 'Volcanites', 'Plutonites'], 'None')
                
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
        self.worker = PlotWorker(normalized_df, self.current_mode, 
                                 self.current_highlight, self.current_classification)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, normalized_df, mode):
        sender = self.sender()
        if sender != self.worker:
            if hasattr(self, 'old_workers') and sender in self.old_workers:
                self.old_workers.remove(sender)
            return
            
        self.worker = None
        
        if error_msg:
            self.stack.setCurrentIndex(0)
            QMessageBox.critical(self, "Error", error_msg)
            return
            
        if normalized_df is not None:
            self.normalized_df = normalized_df
            if self.current_mode != mode:
                self.current_mode = mode
                self.current_highlight = 'None'
                self.current_classification = 'None'
                self.plot_view.update_highlight_options(mode)
                self.plot_view.classification_toggle.update_options(['None', 'Volcanites', 'Plutonites'], 'None')
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_qapf(self.normalized_df, mode=self.current_mode, dark_mode=False, 
                              highlight_axis=self.current_highlight, classification=self.current_classification),
            "qapf_diagram.png"
        )
