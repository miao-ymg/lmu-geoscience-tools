import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFileDialog, QMessageBox,
    QStackedWidget, QSplitter
)
from gui.components.action_button import ActionButton
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

class BasePlotView(QWidget):
    """
    A unified base view for all plotting tools.
    Provides standardized UI layout, buttons, and download logic.
    """
    def __init__(self, on_new_sample, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(28)
        
        # 1. Top layout for optional tool-specific controls (e.g. QAPF/TAS toggles)
        self.top_container = QWidget()
        self.top_layout = QHBoxLayout(self.top_container)
        self.top_layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.top_container)
        
        # 2. Main canvas area
        self.canvas_container = QStackedWidget()
        self.layout.addWidget(self.canvas_container, stretch=1)
        
        # 3. Optional note space below canvas
        self.note_label = QLabel(" ")
        self.note_label.setFixedHeight(20)
        self.note_label.setObjectName("PlotNoteLabel")
        self.note_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.note_label)
        
        self.layout.addSpacing(15)
        
        # 4. Standard bottom buttons
        self.btn_layout = QHBoxLayout()
        self.btn_layout.setSpacing(10)
        
        self.download_btn = ActionButton("Download Image", style_type="primary")
        self.download_btn.setObjectName("PlotDownloadBtn")
        self.btn_layout.addWidget(self.download_btn)
        
        self.new_sample_btn = ActionButton("New sample", style_type="secondary")
        self.new_sample_btn.setObjectName("PlotNewSampleBtn")
        self.new_sample_btn.clicked.connect(on_new_sample)
        self.btn_layout.addWidget(self.new_sample_btn)
        
        self.layout.addLayout(self.btn_layout)
        
        self.current_fig = None
        self.canvas = None
        
    def add_top_widget(self, widget):
        """Adds a tool-specific control widget above the canvas."""
        self.top_layout.addWidget(widget)
        
    def add_top_stretch(self):
        """Pushes top controls to the left by adding a stretch."""
        self.top_layout.addStretch()

    def set_note(self, text):
        """Displays a standardized warning/note below the canvas."""
        self.note_label.setText(text)
        
    def set_plot(self, fig):
        """Embeds the generated matplotlib Figure into the UI."""
        self.current_fig = fig
        old_canvas = getattr(self, 'canvas', None)
        
        self.canvas = FigureCanvas(fig)
        self.canvas.setObjectName("PlotCanvas")
        self.canvas_container.addWidget(self.canvas)
        self.canvas_container.setCurrentWidget(self.canvas)
        
        if old_canvas:
            self.canvas_container.removeWidget(old_canvas)
            old_canvas.deleteLater()
        
    def handle_download(self, parent_widget, generate_light_fig_func, default_filename):
        """
        Standardized download handler.
        generate_light_fig_func should take no arguments and return a Figure styled for light mode.
        """
        if not self.current_fig:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Save Plot",
            os.path.expanduser(f"~/Desktop/{default_filename}"),
            "PNG Images (*.png);;PDF Documents (*.pdf);;SVG Graphics (*.svg)"
        )
        
        if file_path:
            try:
                # Generate a clean, light-mode figure specifically for export
                fig = generate_light_fig_func()
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(parent_widget, "Success", f"Plot successfully saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(parent_widget, "Error", f"Failed to save plot:\n{str(e)}")
