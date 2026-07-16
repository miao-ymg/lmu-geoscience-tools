import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
def plot_raman(df, dark_mode=False):
    """
    Plots Raman spectra from the DataFrame.
    """
    if dark_mode:
        bg_color = '#1e1e1e'
        line_color = 'white'
        text_color = 'white'
        grid_color = '#444444'
        accent_color = '#a6e3a1'
    else:
        bg_color = 'white'
        line_color = 'black'
        text_color = 'black'
        grid_color = '#dddddd'
        accent_color = '#40a02b'
        
    fig = plt.figure(figsize=(10, 6), facecolor=bg_color)
    ax = fig.add_subplot(111)
    
    # Style the axes
    ax.set_facecolor(bg_color)
    for spine in ax.spines.values():
        spine.set_color(text_color)
    
    ax.tick_params(colors=text_color, which='both')
    
    # Plot the data
    ax.plot(df['Raman Shift'], df['Intensity'], color=accent_color, linewidth=1.5)
    
    # Labels
    ax.set_xlabel('Raman Shift (cm$^{-1}$)', color=text_color, fontsize=12, fontweight='bold', labelpad=15)
    ax.set_ylabel('Intensity (Counts)', color=text_color, fontsize=12, fontweight='bold', labelpad=15)
    
    # Grid
    ax.grid(True, linestyle='--', color=grid_color, alpha=0.5, zorder=0)
    
    # Ticks formatting
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
    
    # Set limits so plot sticks to the axes
    min_x, max_x = df['Raman Shift'].min(), df['Raman Shift'].max()
    min_y = df['Intensity'].min()
    
    ax.set_xlim(min_x, max_x)
    ax.set_ylim(bottom=min_y)
    
    # Fill exactly down to the bottom
    ax.fill_between(df['Raman Shift'], df['Intensity'], min_y, 
                    color=accent_color, alpha=0.1, zorder=1)
    
    fig.tight_layout()
    return fig
