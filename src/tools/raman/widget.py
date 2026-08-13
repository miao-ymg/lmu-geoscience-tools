from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal, QSettings
import os

from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView
from .data import load_and_validate_data
from .plot import plot_raman

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, dict)
    
    def __init__(self, dfs_dict):
        super().__init__()
        self.dfs_dict = dfs_dict
        
    def run(self):
        try:
            fig = plot_raman(self.dfs_dict, dark_mode=True)
            self.finished.emit(fig, "", self.dfs_dict)
        except Exception as e:
            self.finished.emit(None, f"Error generating plot: {str(e)}", self.dfs_dict)

class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download):
        super().__init__(on_new_sample)
        self.download_btn.clicked.connect(on_download)

class RamanWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.stack = QStackedWidget()
        instructions = (
            "<div><p style='margin-bottom: 12px;'><b>Requirements:</b><br>File must contain lines with exactly two numbers:</p>"
            "<p style='margin-top: 0px; margin-bottom: 8px;'>&bull; Raman Shift</p>"
            "<p style='margin-top: 0px; margin-bottom: 0px;'>&bull; Intensity</p></div>"
        )
        self.upload_view = UploadBox(
            self.on_file_selected, 
            self.on_generate_clicked,
            drop_text="Drag & Drop your text file here\nor click to browse",
            file_filter="Text Files (*.txt);;All Files (*.*)",
            multi_file=True,
            instructions=instructions
        )
        self.plot_view = PlotView(self.show_upload, self.download_plot)
        self.loading_overlay = PanelOverlay()
        
        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        layout.addWidget(self.stack)
        
        self.current_file_paths = []
        self.dfs_dict = {}
        
        self.worker = None
        self.old_workers = []
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_paths):
        self.current_file_paths = file_paths
        
    def on_generate_clicked(self):
        if not self.current_file_paths:
            return
            
        dfs_dict = {}
        try:
            for file_path in self.current_file_paths:
                df, error = load_and_validate_data(file_path)
                if error:
                    QMessageBox.critical(self, "Error", f"Error in file {os.path.basename(file_path)}: {error}")
                    return
                dfs_dict[os.path.basename(file_path)] = df
            self.dfs_dict = dfs_dict
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return
            
        self.start_worker(dfs_dict=self.dfs_dict, show_loading=True)
            
    def start_worker(self, dfs_dict, show_loading=True):
        if self.worker is not None and self.worker.isRunning():
            self.old_workers.append(self.worker)
            
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(dfs_dict)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, dfs_dict):
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
            
        if dfs_dict is not None:
            self.dfs_dict = dfs_dict
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_raman(self.dfs_dict, dark_mode=False),
            "raman_spectra.png"
        )
