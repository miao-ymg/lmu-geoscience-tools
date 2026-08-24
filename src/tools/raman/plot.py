import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from theme import colors

def find_peaks(x, y, window_size=50, prominence_factor=3.0):
    """
    Finds extreme spikes (peaks) by comparing the signal to a local moving average.
    """
    peaks = []
    if len(y) < window_size:
        return peaks
        
    # Calculate a simple moving average to act as baseline
    window = np.ones(window_size) / window_size
    baseline = np.convolve(y, window, mode='same')
    
    # Calculate how much each point stands above the baseline
    prominence = y - baseline
    
    # We only care about the middle part to avoid convolution edge artifacts
    edge = window_size // 2
    valid_prominence = prominence[edge:-edge]
    
    # Calculate threshold based on the variance of the prominence (noise level)
    positive_prom = valid_prominence[valid_prominence > 0]
    if len(positive_prom) == 0:
        return peaks
        
    threshold = np.mean(positive_prom) + prominence_factor * np.std(positive_prom)
    
    # Find local maxima in the original signal that also exceed the prominence threshold
    for i in range(edge, len(y) - edge):
        if y[i] > y[i - 1] and y[i] > y[i + 1] and prominence[i] > threshold:
            peaks.append((x[i], y[i]))
            
    return peaks

def plot_raman(dfs_dict, dark_mode=False):
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
    else:
        bg_color = colors['plot-bg-light']
        text_color = colors['plot-text-light']
        line_color = colors['plot-line-light']
        grid_color = colors['plot-grid-light']
        base_accent = colors['plot-accent-light']
        
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
        peaks = find_peaks(x_vals, y_vals, window_size=50, prominence_factor=4.0)
        
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
    
    # Set limits so plot sticks to the axes
    if min_x != float('inf'):
        ax.set_xlim(min_x, max_x)
        ax.set_ylim(bottom=min_y)
    
    fig.tight_layout()
    return fig
