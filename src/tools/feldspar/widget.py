import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from gui.components.upload_box import UploadBox
from gui.components.loading_overlays import PanelOverlay
from gui.components.plot_view import BasePlotView
from .data import load_and_validate_data, compute_feldspar_endmembers
from .plot import plot_feldspar


class PlotWorker(QThread):
    finished = pyqtSignal(object, str, object)  # fig, error_msg, endmembers_df
    
    def __init__(self, endmembers_df, parent=None):
        super().__init__(parent)
        self.endmembers_df = endmembers_df
        
    def run(self):
        error_msg = None
        fig = None
        try:
            if self.endmembers_df is not None:
                fig = plot_feldspar(self.endmembers_df, dark_mode=True)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            
        self.finished.emit(fig, error_msg, self.endmembers_df)


class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download):
        super().__init__(on_new_sample)
        self.download_btn.clicked.connect(on_download)
        self.set_note("Note: These classifications are only approximations and could therefore be inaccurate.")


class FeldsparWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)

        self.stack = QStackedWidget()
        instructions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'column_aliases.yml')
        from utils.instructions import get_instructions_data
        instructions = get_instructions_data(instructions_path)
        self.upload_view = UploadBox(self.on_file_selected, self.on_generate_clicked, instructions=instructions)
        self.plot_view = PlotView(self.show_upload, self.download_plot)
        self.loading_overlay = PanelOverlay()

        self.stack.addWidget(self.upload_view)   # Index 0
        self.stack.addWidget(self.plot_view)     # Index 1
        self.stack.addWidget(self.loading_overlay) # Index 2
        layout.addWidget(self.stack)

        self.current_file_path = None
        self.endmembers_df = None
        
        self.worker = None

    # ── Callbacks ────────────────────────────────────────────────────

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
            endmembers_df = compute_feldspar_endmembers(df)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            return
            
        # Show disclaimer only when a new file was successfully processed
        if self.endmembers_df is None or not self.endmembers_df.equals(endmembers_df):
            QMessageBox.information(self, "Disclaimer", "Please note that you are responsible for providing correct raw Feldspar data. This tool only handles the visualization.")
            
        self.start_worker(endmembers_df=endmembers_df, show_loading=True)

    def refresh_plot(self):
        if self.endmembers_df is None:
            return
        self.start_worker(endmembers_df=self.endmembers_df, show_loading=False)
            
    def start_worker(self, endmembers_df, show_loading=True):
        if self.worker is not None and self.worker.isRunning():
            self.worker.finished.disconnect(self.on_worker_finished)
            self.worker.finished.connect(self.worker.deleteLater)
            
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(endmembers_df, parent=self)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, endmembers_df):
        sender = self.sender()
        if sender != self.worker:
            sender.deleteLater()
            return
            
        if endmembers_df is not None:
            self.endmembers_df = endmembers_df
        
        self.worker = None
        
        if error_msg:
            self.stack.setCurrentIndex(0)
            QMessageBox.critical(self, "Error", error_msg)
            return
            
        if fig:
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_feldspar(self.endmembers_df, dark_mode=False),
            "feldspar_diagram.png"
        )
