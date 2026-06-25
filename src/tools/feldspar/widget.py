import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QMessageBox, QFileDialog, QLabel
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

from gui.components.upload_box import UploadBox
from .data import load_and_validate_data, compute_feldspar_endmembers
from .plot import plot_feldspar


class PlotView(QWidget):
    def __init__(self, on_new_sample, on_download):
        super().__init__()
        layout = QVBoxLayout(self)

        self.canvas_layout = QVBoxLayout()
        layout.addLayout(self.canvas_layout, stretch=1)

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

        layout.addLayout(btn_layout)
        self.current_fig = None
        self.canvas = None

    def set_plot(self, fig):
        self.current_fig = fig
        for i in reversed(range(self.canvas_layout.count())):
            w = self.canvas_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.canvas = FigureCanvas(fig)
        self.canvas.setStyleSheet("background-color: transparent;")
        self.canvas_layout.addWidget(self.canvas)

        warning_label = QLabel("Note: These classifications are only approximations and could therefore be inaccurate.")
        warning_label.setStyleSheet("color: #ffaa00; font-style: italic; font-size: 13px;")
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_layout.addWidget(warning_label)
        self.canvas_layout.addSpacing(15)


class FeldsparWidget(QWidget):
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
        self.endmembers_df = None

    # ── Callbacks ────────────────────────────────────────────────────

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

        QMessageBox.information(self, "Disclaimer", "Please note that you are responsible for providing correct raw Feldspar data. This tool only handles the visualization.")

        try:
            self.endmembers_df = compute_feldspar_endmembers(df)
            self.refresh_plot()
            self.stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "Processing Error",
                                 f"An error occurred while processing the data: {e}")

    def refresh_plot(self):
        if self.endmembers_df is None:
            return
        try:
            fig = plot_feldspar(self.endmembers_df, dark_mode=True)
            self.plot_view.set_plot(fig)
        except Exception as e:
            QMessageBox.critical(self, "Plotting Error",
                                 f"An error occurred while generating the plot: {e}")

    def download_plot(self):
        if self.endmembers_df is None or not self.current_file_path:
            return

        base_name = os.path.splitext(os.path.basename(self.current_file_path))[0]
        default_name = f"{base_name}_feldspar_plot.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Plot", default_name,
            "PNG Images (*.png);;PDF Files (*.pdf)"
        )
        if file_path:
            try:
                fig = plot_feldspar(self.endmembers_df, dark_mode=False)
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "Success", "Plot saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not save plot: {e}")
