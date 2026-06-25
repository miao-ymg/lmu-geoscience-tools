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
from .data import load_and_validate_data, normalize_tas
from .plot import plot_tas

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)  # fig, error_msg, normalized_df
    
    def __init__(self, file_path, normalized_df, classification):
        super().__init__()
        self.file_path = file_path
        self.normalized_df = normalized_df
        self.classification = classification
        
    def run(self):
        error_msg = None
        fig = None
        try:
            if self.normalized_df is None and self.file_path:
                df, error = load_and_validate_data(self.file_path)
                if error:
                    self.finished.emit(None, error, None)
                    return
                self.normalized_df = normalize_tas(df)
                
            if self.normalized_df is not None:
                fig = plot_tas(self.normalized_df, dark_mode=True, rock_type=self.classification)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.normalized_df)

class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download, on_classification_changed):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Toggles layout
        toggles_layout = QHBoxLayout()
        self.classification_toggle = ToggleGroup("Classification:", ['Volcanites', 'Plutonites'], 'Volcanites')
        self.classification_toggle.selectionChanged.connect(on_classification_changed)
        toggles_layout.addWidget(self.classification_toggle)
        toggles_layout.addStretch()
        self.layout.addLayout(toggles_layout)
        
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
            
        self.start_worker(file_path=self.current_file_path, show_loading=True)

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        self.start_worker(normalized_df=self.normalized_df, show_loading=False)
            
    def start_worker(self, file_path=None, normalized_df=None, show_loading=True):
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(file_path, normalized_df, self.current_classification)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, normalized_df):
        self.worker = None
        
        if error_msg:
            QMessageBox.critical(self, "Error", error_msg)
            return
            
        if normalized_df is not None:
            self.normalized_df = normalized_df
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        if self.normalized_df is None or not self.current_file_path:
            return
            
        filename = os.path.basename(self.current_file_path)
        base_name, _ = os.path.splitext(filename)
        
        default_save_name = f"{base_name}_tas_plot.png"
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", default_save_name, "PNG Images (*.png);;PDF Files (*.pdf)"
        )
        if file_path:
            try:
                # Generate light-theme plot for saving
                fig_to_save = plot_tas(self.normalized_df, dark_mode=False, rock_type=self.current_classification)
                fig_to_save.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", "Plot successfully saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the plot: {str(e)}")
