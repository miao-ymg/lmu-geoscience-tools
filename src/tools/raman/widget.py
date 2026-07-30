from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal

from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView
from .data import load_and_validate_data
from .plot import plot_raman

class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)  # fig, error_msg, df
    
    def __init__(self, df):
        super().__init__()
        self.df = df
        
    def run(self):
        error_msg = None
        fig = None
        try:
            if self.df is not None:
                fig = plot_raman(self.df, dark_mode=True)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.df)

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
        self.upload_view = UploadBox(
            self.on_file_selected, 
            self.on_generate_clicked,
            drop_text="Drag & Drop your Raman Text file (.txt) here\nor click to browse",
            file_filter="Text Files (*.txt);;All Files (*)"
        )
        self.plot_view = PlotView(self.show_upload, self.download_plot)
        self.loading_overlay = PanelOverlay()
        
        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        layout.addWidget(self.stack)
        
        self.current_file_path = None
        self.df = None
        
        self.worker = None
        self.old_workers = []
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_path):
        self.current_file_path = file_path
        
    def on_generate_clicked(self):
        if not self.current_file_path:
            return
            
        try:
            df, error = load_and_validate_data(self.current_file_path)
            if error:
                QMessageBox.critical(self, "Error", error)
                return
            self.df = df
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return
            
        self.start_worker(df=self.df, show_loading=True)
            
    def start_worker(self, df, show_loading=True):
        if self.worker is not None and self.worker.isRunning():
            self.old_workers.append(self.worker)
            
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(df)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, df):
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
            
        if df is not None:
            self.df = df
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_raman(self.df, dark_mode=False),
            "raman_spectra.png"
        )
