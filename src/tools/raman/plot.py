import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from theme import colors
from scipy.signal import find_peaks as scipy_find_peaks, savgol_filter

def find_peaks(x, y, window_size=50, prominence_factor=1.5):
    """
    Finds real Raman spectrum peaks while ignoring high-frequency noise spikes and broad background curves.
    """
    if len(y) < 10:
        return []
        
    # 1. Smooth signal with a light Savitzky-Golay filter to eliminate single-point noise spikes
    wl = 9 if len(y) >= 9 else (len(y) if len(y) % 2 != 0 else len(y) - 1)
    if wl >= 5:
        y_smooth = savgol_filter(y, window_length=wl, polyorder=3)
    else:
        y_smooth = y
        
    # 2. Estimate high-frequency noise standard deviation
    noise_std = np.std(y - y_smooth)
    
    # 3. Dynamic prominence threshold: at least 6x noise level and at least 1.5% of total intensity range
    signal_span = np.ptp(y)
    min_prom = max(6.0 * noise_std, 0.015 * signal_span)
    
    # Minimum distance: ~20 cm-1
    x_step = np.median(np.diff(x)) if len(x) > 1 else 1.0
    min_dist_pts = max(3, int(20 / x_step)) if x_step > 0 else 5
    
    peaks_idx, _ = scipy_find_peaks(
        y_smooth,
        prominence=min_prom,
        distance=min_dist_pts,
        wlen=int(200 / x_step) if x_step > 0 else 50
    )
    
    return [(x[i], y[i]) for i in peaks_idx]

def plot_raman(dfs_dict, dark_mode=False, selected_x=None):
    """
    Plots Raman spectra from a dictionary of DataFrames.
    dfs_dict: {filename: DataFrame}
    """
    if dark_mode:
        bg_color = colors['plot-bg-dark']
        text_color = colors['plot-text-dark']
        line_color = colors['plot-line-dark']
        grid_color = colors['plot-grid-dark']
        base_accent = colors['plot-accent-dark']
        point_color = colors['plot-point-dark']
        edge_color = colors['plot-edge-dark']
    else:
        bg_color = colors['plot-bg-light']
        text_color = colors['plot-text-light']
        line_color = colors['plot-line-light']
        grid_color = colors['plot-grid-light']
        base_accent = colors['plot-accent-light']
        point_color = colors['plot-point-light']
        edge_color = colors['plot-edge-light']
        
    fig = plt.figure(figsize=(10, 6), facecolor=bg_color)
    ax = fig.add_subplot(111)
    
    # Style the axes
    ax.set_facecolor(bg_color)
    for spine in ax.spines.values():
        spine.set_color(text_color)
    
    ax.tick_params(colors=text_color, which='both')
    
    # Use tab10 colormap for multiple lines, falling back to base_accent if only 1 file
    line_colors = plt.get_cmap('tab10').colors
    
    min_x, max_x = float('inf'), float('-inf')
    
    if dfs_dict:
        global_min_y = min(df['Intensity'].min() for df in dfs_dict.values())
    else:
        global_min_y = float('inf')
        
    min_y = global_min_y
    
    # Process each file
    for idx, (filename, df) in enumerate(dfs_dict.items()):
        color = base_accent if len(dfs_dict) == 1 else line_colors[idx % len(line_colors)]
        
        # Plot the data
        ax.plot(df['Raman Shift'], df['Intensity'], color=color, linewidth=1.5, label=filename)
        
        # Update limits
        min_x = min(min_x, df['Raman Shift'].min())
        max_x = max(max_x, df['Raman Shift'].max())
        
        # Find and label peaks
        y_vals = df['Intensity'].values
        x_vals = df['Raman Shift'].values
        
        # Use our updated local-baseline peak finder
        peaks = find_peaks(x_vals, y_vals, window_size=50, prominence_factor=1.5)
        
        # Optional: Filter out peaks that are too close to each other, taking the highest
        # (This avoids clumping of labels if a peak has noise)
        filtered_peaks = []
        min_distance = (df['Raman Shift'].max() - df['Raman Shift'].min()) * 0.02 # 2% of total x-axis range
        
        for px, py in peaks:
            # Check if there's an existing peak too close
            too_close = False
            for i, (fx, fy) in enumerate(filtered_peaks):
                if abs(px - fx) < min_distance:
                    too_close = True
                    # If this peak is higher, replace the existing one
                    if py > fy:
                        filtered_peaks[i] = (px, py)
                    break
            
            if not too_close:
                filtered_peaks.append((px, py))
                
        for px, py in filtered_peaks:
            ax.annotate(f"{int(round(px))}", 
                        xy=(px, py), 
                        xytext=(0, 5), 
                        textcoords="offset points", 
                        ha='center', va='bottom', 
                        color=text_color, 
                        fontsize=9)
        
        # Fill under the curve slightly for aesthetics
        ax.fill_between(df['Raman Shift'], df['Intensity'], global_min_y, 
                        color=color, alpha=0.1, zorder=1)
    
    # Legend
    if len(dfs_dict) > 1:
        ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color, loc='upper right')

    # Labels
    ax.set_xlabel('Raman Shift (cm$^{-1}$)', color=text_color, fontsize=12, fontweight='bold', labelpad=15)
    ax.set_ylabel('Intensity (Counts)', color=text_color, fontsize=12, fontweight='bold', labelpad=15)
    
    # Grid
    ax.grid(True, linestyle='--', color=grid_color, alpha=0.5, zorder=0)
    
    # Ticks formatting
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
    
    # Vertical tracking cursor line behind graph (zorder=0.8)
    cursor_line = ax.axvline(x=0, color=line_color, linestyle='--', linewidth=1.2, alpha=0.75, zorder=0.8, visible=False, animated=True)
    ax.cursor_line = cursor_line

    # Hover cross marker on curves: larger, bright white/text-color, prominent
    cross_color = "#ffffff" if dark_mode else "#000000"
    hover_cross = ax.scatter([], [], color=cross_color, s=150, linewidths=2.2, zorder=5.5, marker='+', visible=False, animated=True)
    ax.hover_cross = hover_cross

    # Marker for selected points (yellow circle with edge, as used in other tools)
    sel_scatter = ax.scatter([], [], color=point_color, edgecolors=edge_color, s=100, linewidths=1.5, zorder=6, marker='o', animated=True)
    ax.selected_scatter = sel_scatter

    # Text annotation displaying the Raman shift x-value cleanly below the selected point
    val_text = ax.annotate("", xy=(0, 0), xytext=(0, -18), textcoords="offset points",
                           color=text_color, fontsize=9, fontweight='bold', ha='center', va='top', 
                           bbox=dict(boxstyle='round,pad=0.25', facecolor=bg_color if bg_color != 'none' else '#161b22', edgecolor=line_color, alpha=0.9),
                           visible=False, animated=True, zorder=10, clip_on=False)
    ax.val_text = val_text

    # If an initial selected_x is passed, position marker and text
    if selected_x is not None:
        pts_x = []
        pts_y = []
        for df in dfs_dict.values():
            xs = df['Raman Shift'].values
            ys = df['Intensity'].values
            if len(xs) > 0 and xs.min() <= selected_x <= xs.max():
                y_val = float(np.interp(selected_x, xs, ys))
                pts_x.append(selected_x)
                pts_y.append(y_val)
        if pts_x:
            sel_scatter.set_offsets(np.column_stack([pts_x, pts_y]))
            val_text.xy = (pts_x[0], pts_y[0])
            val_text.set_text(f"{int(round(pts_x[0]))} cm⁻¹")
            if min_x != float('inf') and max_x > min_x:
                norm_x = (pts_x[0] - min_x) / (max_x - min_x)
                if norm_x < 0.12:
                    val_text.set_ha('left')
                    val_text.xyann = (8, -18)
                elif norm_x > 0.88:
                    val_text.set_ha('right')
                    val_text.xyann = (-8, -18)
            val_text.set_visible(True)

    # Set limits so plot sticks to the axes
    if min_x != float('inf'):
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(bottom=min_y)
    
    fig.tight_layout()
    return fig
