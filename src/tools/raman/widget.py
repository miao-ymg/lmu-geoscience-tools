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
    
    def __init__(self, dfs_dict, parent=None):
        super().__init__(parent)
        self.dfs_dict = dfs_dict
        
    def run(self):
        try:
            fig = plot_raman(self.dfs_dict, dark_mode=True)
            self.finished.emit(fig, "", self.dfs_dict)
        except Exception as e:
            self.finished.emit(None, f"Error generating plot: {str(e)}", self.dfs_dict)

import numpy as np

class PlotView(BasePlotView):
    def __init__(self, on_new_sample, on_download):
        super().__init__(on_new_sample)
        self.download_btn.clicked.connect(on_download)
        self.set_note("Note: The detected peak positions are based on statistical signal-processing algorithms and may be inaccurate.", key="note_raman")
        self.dfs_dict = {}
        self.selected_x = None
        self._cid_motion = None
        self._cid_press = None
        self._cid_leave = None
        
    def set_data(self, dfs_dict):
        self.dfs_dict = dfs_dict
        self.selected_x = None
        
    def set_plot(self, fig):
        super().set_plot(fig)
        self._bg = None
        self._is_dragging = False
        if self.canvas is not None:
            self._cid_draw = self.canvas.mpl_connect('draw_event', self.on_draw)
            self._cid_motion = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self._cid_press = self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
            self._cid_release = self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
            self._cid_leave = self.canvas.mpl_connect('figure_leave_event', self.on_mouse_leave)

    def on_draw(self, event):
        if self.canvas is not None and self.current_fig and self.current_fig.axes:
            ax = self.current_fig.axes[0]
            self._bg = self.canvas.copy_from_bbox(ax.bbox)

    def _get_points_for_x(self, x_val):
        pts_x = []
        pts_y = []
        for df in self.dfs_dict.values():
            xs = df['Raman Shift'].values
            ys = df['Intensity'].values
            if len(xs) > 0 and xs.min() <= x_val <= xs.max():
                y_val = float(np.interp(x_val, xs, ys))
                pts_x.append(x_val)
                pts_y.append(y_val)
        return pts_x, pts_y

    def _update_val_text(self, ax, val_text, px, py):
        val_text.xy = (px, py)
        val_text.set_text(f"{int(round(px))} cm⁻¹")
        
        # Determine placement based on closeness to axes boundaries
        xlim = ax.get_xlim()
        x_span = xlim[1] - xlim[0] if xlim[1] != xlim[0] else 1.0
        norm_x = (px - xlim[0]) / x_span

        # Adjust horizontal alignment near left/right edges so it doesn't get cut by spine
        if norm_x < 0.12:
            ha = 'left'
            dx = 8
        elif norm_x > 0.88:
            ha = 'right'
            dx = -8
        else:
            ha = 'center'
            dx = 0

        # Adjust vertical placement: normally below point, or above if close to bottom
        ylim = ax.get_ylim()
        y_span = ylim[1] - ylim[0] if ylim[1] != ylim[0] else 1.0
        norm_y = (py - ylim[0]) / y_span
        if norm_y < 0.15:
            va = 'bottom'
            dy = 16
        else:
            va = 'top'
            dy = -18

        val_text.set_ha(ha)
        val_text.set_va(va)
        val_text.xyann = (dx, dy)
        val_text.set_visible(True)

    def on_mouse_move(self, event):
        if not self.current_fig or not self.current_fig.axes or self._bg is None:
            return
        ax = self.current_fig.axes[0]
        cursor_line = getattr(ax, 'cursor_line', None)
        hover_cross = getattr(ax, 'hover_cross', None)
        sel_scatter = getattr(ax, 'selected_scatter', None)
        val_text = getattr(ax, 'val_text', None)
        if cursor_line is None or hover_cross is None:
            return
            
        if event.inaxes == ax and event.xdata is not None:
            x_val = event.xdata
            cursor_line.set_xdata([x_val, x_val])
            cursor_line.set_visible(True)

            pts_x, pts_y = self._get_points_for_x(x_val)

            if self._is_dragging:
                # While dragging: update selected yellow marker and value display continuously
                self.selected_x = x_val
                hover_cross.set_visible(False)
                if sel_scatter is not None:
                    if pts_x:
                        sel_scatter.set_offsets(np.column_stack([pts_x, pts_y]))
                        sel_scatter.set_visible(True)
                    else:
                        sel_scatter.set_offsets(np.empty((0, 2)))
                        sel_scatter.set_visible(False)
                if val_text is not None and pts_x:
                    self._update_val_text(ax, val_text, pts_x[0], pts_y[0])
            else:
                # Hovering without press: show bright cross
                if pts_x:
                    hover_cross.set_offsets(np.column_stack([pts_x, pts_y]))
                    hover_cross.set_visible(True)
                else:
                    hover_cross.set_visible(False)

            # Fast blit axes region only
            self.canvas.restore_region(self._bg)
            ax.draw_artist(cursor_line)
            if not self._is_dragging and hover_cross.get_visible():
                ax.draw_artist(hover_cross)
            if sel_scatter is not None and sel_scatter.get_visible():
                ax.draw_artist(sel_scatter)
            if val_text is not None and val_text.get_visible():
                ax.draw_artist(val_text)
            self.canvas.blit(ax.bbox)
        else:
            if not self._is_dragging and (cursor_line.get_visible() or hover_cross.get_visible()):
                cursor_line.set_visible(False)
                hover_cross.set_visible(False)
                self.canvas.restore_region(self._bg)
                if sel_scatter is not None and sel_scatter.get_visible():
                    ax.draw_artist(sel_scatter)
                if val_text is not None and val_text.get_visible():
                    ax.draw_artist(val_text)
                self.canvas.blit(ax.bbox)

    def on_mouse_leave(self, event):
        if not self.current_fig or not self.current_fig.axes or self._bg is None:
            return
        ax = self.current_fig.axes[0]
        cursor_line = getattr(ax, 'cursor_line', None)
        hover_cross = getattr(ax, 'hover_cross', None)
        sel_scatter = getattr(ax, 'selected_scatter', None)
        val_text = getattr(ax, 'val_text', None)
        if not self._is_dragging:
            if cursor_line:
                cursor_line.set_visible(False)
            if hover_cross:
                hover_cross.set_visible(False)
            self.canvas.restore_region(self._bg)
            if sel_scatter is not None and sel_scatter.get_visible():
                ax.draw_artist(sel_scatter)
            if val_text is not None and val_text.get_visible():
                ax.draw_artist(val_text)
            self.canvas.blit(ax.bbox)

    def on_mouse_press(self, event):
        if not self.current_fig or not self.current_fig.axes:
            return
        ax = self.current_fig.axes[0]
        if event.inaxes != ax or event.xdata is None or event.button != 1:
            return
            
        self._is_dragging = True
        x_click = event.xdata
        self.selected_x = x_click
        
        pts_x, pts_y = self._get_points_for_x(x_click)
                
        hover_cross = getattr(ax, 'hover_cross', None)
        if hover_cross:
            hover_cross.set_visible(False)

        sel_scatter = getattr(ax, 'selected_scatter', None)
        if sel_scatter is not None:
            if pts_x:
                sel_scatter.set_offsets(np.column_stack([pts_x, pts_y]))
                sel_scatter.set_visible(True)
            else:
                sel_scatter.set_offsets(np.empty((0, 2)))
                sel_scatter.set_visible(False)

        val_text = getattr(ax, 'val_text', None)
        if val_text is not None and pts_x:
            self._update_val_text(ax, val_text, pts_x[0], pts_y[0])

        if self._bg is not None:
            cursor_line = getattr(ax, 'cursor_line', None)
            self.canvas.restore_region(self._bg)
            if cursor_line is not None and cursor_line.get_visible():
                ax.draw_artist(cursor_line)
            if sel_scatter is not None and sel_scatter.get_visible():
                ax.draw_artist(sel_scatter)
            if val_text is not None and val_text.get_visible():
                ax.draw_artist(val_text)
            self.canvas.blit(ax.bbox)

    def on_mouse_release(self, event):
        if not self._is_dragging:
            return
        self._is_dragging = False
        if event.inaxes and event.xdata is not None:
            self.selected_x = event.xdata
        # Keep selected marker and value display visible, and update view
        if self.canvas is not None and self.current_fig and self.current_fig.axes:
            ax = self.current_fig.axes[0]
            cursor_line = getattr(ax, 'cursor_line', None)
            sel_scatter = getattr(ax, 'selected_scatter', None)
            val_text = getattr(ax, 'val_text', None)
            if self._bg is not None:
                self.canvas.restore_region(self._bg)
                if cursor_line is not None and cursor_line.get_visible():
                    ax.draw_artist(cursor_line)
                if sel_scatter is not None and sel_scatter.get_visible():
                    ax.draw_artist(sel_scatter)
                if val_text is not None and val_text.get_visible():
                    ax.draw_artist(val_text)
                self.canvas.blit(ax.bbox)

class RamanWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        
        self.stack = QStackedWidget()
        instructions = {
            "header": "<b>Requirements:</b> Each measurement point must be given as a line containing two space-separated values. The axis descriptions are given as follows:",
            "bullets": ["<b>Raman Shift</b>", "<b>Intensity</b>"]
        }
        self.upload_view = UploadBox(
            self.on_file_selected, 
            self.on_generate_clicked,
            drop_title="Text",
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

        from utils.i18n import i18n
        i18n.language_changed.connect(lambda _: self.refresh_plot())

    def refresh_plot(self):
        if not self.dfs_dict:
            return
        self.start_worker(dfs_dict=self.dfs_dict, show_loading=False)
        
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
            self.worker.finished.disconnect(self.on_worker_finished)
            self.worker.finished.connect(self.worker.deleteLater)
            
        if show_loading:
            self.stack.setCurrentIndex(2) # Show loading screen
        self.worker = PlotWorker(dfs_dict, parent=self)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()
        
    def on_worker_finished(self, fig, error_msg, dfs_dict):
        sender = self.sender()
        if sender != self.worker:
            sender.deleteLater()
            return
            
        self.worker = None
        
        if error_msg:
            self.stack.setCurrentIndex(0)
            QMessageBox.critical(self, "Error", error_msg)
            return
            
        if dfs_dict is not None:
            self.dfs_dict = dfs_dict
            
        if fig:
            self.plot_view.set_data(self.dfs_dict)
            self.plot_view.set_plot(fig)
            self.stack.setCurrentIndex(1)

    def download_plot(self):
        self.plot_view.handle_download(
            self,
            lambda: plot_raman(self.dfs_dict, dark_mode=False, selected_x=self.plot_view.selected_x),
            "raman_spectra.png"
        )
