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

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object, str)  # fig, error_msg, normalized_df, mode
    
    def __init__(self, file_path, normalized_df, mode, highlight, classification):
        super().__init__()
        self.file_path = file_path
        self.normalized_df = normalized_df
        self.mode = mode
        self.highlight = highlight
        self.classification = classification
        
    def run(self):
        error_msg = None
        fig = None
        mode = self.mode
        try:
            if self.normalized_df is None and self.file_path:
                df, mode, error = load_and_validate_data(self.file_path)
                if error:
                    self.finished.emit(None, error, None, mode)
                    return
                self.normalized_df = normalize_qapf(df)
                
            if self.normalized_df is not None:
                fig = plot_qapf(self.normalized_df, mode=mode, dark_mode=True, 
                                highlight_axis=self.highlight, classification=self.classification)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.normalized_df, mode)

class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download, on_highlight_changed, on_classification_changed):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
        # Toggles
        toggles_layout = QHBoxLayout()
        
        self.highlight_toggle = ToggleGroup("Highlight Axis:", ['None', 'A', 'P'], 'None')
        self.classification_toggle = ToggleGroup("Classification:", ['None', 'Volcanites', 'Plutonites'], 'None')
        
        self.highlight_toggle.selectionChanged.connect(on_highlight_changed)
        self.classification_toggle.selectionChanged.connect(on_classification_changed)
        
        toggles_layout.addWidget(self.highlight_toggle)
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
        
        self.update_highlight_options('QAPF')
        
    def update_highlight_options(self, mode):
        options = ['None', 'A', 'P']
        if mode in ['QAPF', 'QAP']:
            options.insert(1, 'Q')
        if mode in ['QAPF', 'APF']:
            options.append('F')
        self.highlight_toggle.update_options(options, 'None')

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
            
        self.start_worker(file_path=self.current_file_path, show_loading=True)

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        self.start_worker(normalized_df=self.normalized_df, show_loading=False)
            
    def start_worker(self, file_path=None, normalized_df=None, show_loading=True):
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(file_path, normalized_df, self.current_mode, 
                                 self.current_highlight, self.current_classification)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, normalized_df, mode):
        self.worker = None
        
        if error_msg:
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
                fig_to_save = plot_qapf(self.normalized_df, mode=self.current_mode, dark_mode=False, 
                                        highlight_axis=self.current_highlight, classification=self.current_classification)
                fig_to_save.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", "Plot successfully saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the plot: {str(e)}")
