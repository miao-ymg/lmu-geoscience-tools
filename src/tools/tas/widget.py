import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFileDialog, 
    QStackedWidget, QMessageBox, QHBoxLayout
)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from gui.components.upload_box import UploadBox
from .data import load_and_validate_data, normalize_tas
from .plot import plot_tas

class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download):
        super().__init__()
        self.layout = QVBoxLayout(self)
        
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
        self.plot_view = PlotView(self.show_upload, self.download_plot)
        
        self.stack.addWidget(self.upload_view)
        self.stack.addWidget(self.plot_view)
        
        layout.addWidget(self.stack)
        
        self.current_file_path = None
        self.normalized_df = None
        
    def show_upload(self):
        self.upload_view.reset()
        self.stack.setCurrentIndex(0)
        
    def on_file_selected(self, file_path):
        self.current_file_path = file_path
        
    def on_generate_clicked(self):
        if not self.current_file_path:
            return
            
        df, error = load_and_validate_data(self.current_file_path)
        
        if error:
            QMessageBox.warning(self, "Data Error", error)
            return
            
        try:
            self.normalized_df = normalize_tas(df)
            self.refresh_plot()
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", f"An error occurred while generating the plot: {str(e)}")

    def refresh_plot(self):
        if self.normalized_df is None:
            return
        try:
            fig = plot_tas(self.normalized_df, dark_mode=True)
            self.plot_view.set_plot(fig)
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error", f"An error occurred while regenerating the plot: {str(e)}")

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
                fig_to_save = plot_tas(self.normalized_df, dark_mode=False)
                fig_to_save.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", "Plot successfully saved!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save the plot: {str(e)}")
