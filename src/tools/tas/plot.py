import matplotlib.pyplot as plt

def plot_tas(normalized_df, dark_mode=False):
    """
    Plots a TAS (Total Alkali-Silica) diagram using pyrolite.
    Returns a matplotlib Figure object.
    """
    if dark_mode:
        bg_color = '#1e1e1e' # Pure neutral dark grey
        line_color = '#e0e0e0'
        text_color = '#e0e0e0'
        point_color = 'orange' 
        edge_color = '#1e1e1e'
    else:
        bg_color = 'white'
        line_color = 'black'
        text_color = 'black'
        point_color = 'orange'
        edge_color = 'black'

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    # Use pyrolite's TAS template. Imported locally to avoid GUI freezing on startup.
    from pyrolite.plot.templates import TAS
    ax = TAS(ax=ax, add_labels=True, which_labels='volcanic', fontsize=8, linewidth=1.0, color=line_color)
    
    # Update label text colors
    for t in ax.texts:
        t.set_color(text_color)
        
    # Update patch edge colors for classification lines
    for p in ax.patches:
        p.set_edgecolor(line_color)
    
    # Since pyrolite's TAS might use its own colors for lines and text, we can override if needed, 
    # but the simplest is to just apply our text color to spines and ticks
    
    if not normalized_df.empty:
        # Plot points
        ax.scatter(normalized_df['SiO2'], normalized_df['Total_Alkali'], 
                   color=point_color, edgecolors=edge_color, s=100, zorder=5, marker='o')
    
    # Configure axis styling
    ax.set_xlabel("SiO$_2$ (wt%)", color=text_color, fontweight='bold', fontsize=12)
    ax.set_ylabel("Na$_2$O + K$_2$O (wt%)", color=text_color, fontweight='bold', fontsize=12)
    
    ax.tick_params(colors=text_color, which='both')
    for spine in ax.spines.values():
        spine.set_color(line_color)
        
    fig.tight_layout()
    return fig
