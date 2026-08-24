import matplotlib.pyplot as plt
import pyrolite.plot
from theme import colors
from tools.common.plot_utils import draw_sample_points

def plot_tas(normalized_df, dark_mode=False, rock_type='Volcanites'):
    if dark_mode:
        text_color = colors['plot-text-dark']
        line_color = colors['plot-line-dark']
        bg_color = colors['plot-bg-dark']
        point_color = colors['plot-point-dark']
        edge_color = colors['plot-edge-dark']
    else:
        bg_color = colors['plot-bg-light']
        text_color = colors['plot-text-light']
        line_color = colors['plot-line-light']
        point_color = colors['plot-point-light']
        edge_color = colors['plot-edge-light']

    class_line_color = '#5a6270' if dark_mode else colors['plot-line-light']

    fig, ax = plt.subplots(figsize=(10, 7), facecolor=bg_color)
    ax.set_facecolor(bg_color)
    
    # Use pyrolite's TAS template. Imported locally to avoid GUI freezing on startup.
    from pyrolite.plot.templates import TAS
    which_labels = 'volcanic' if rock_type == 'Volcanites' else 'intrusive'
    ax = TAS(ax=ax, add_labels=True, which_labels=which_labels, fontsize=8, linewidth=1.0, color=class_line_color)
    
    # Update label text colors
    for t in ax.texts:
        t.set_color(text_color)
        
    # Update patch edge colors for classification lines
    for p in ax.patches:
        p.set_edgecolor(class_line_color)
    
    # Since pyrolite's TAS might use its own colors for lines and text, we can override if needed, 
    # but the simplest is to just apply our text color to spines and ticks
    
    if not normalized_df.empty:
        # Plot points
        draw_sample_points(ax, normalized_df['SiO2'], normalized_df['Total_Alkali'], 
                           point_color=point_color, edge_color=edge_color)
    
    # Configure axis styling
    ax.set_xlabel("SiO$_2$ (wt%)", color=text_color, fontweight='bold', fontsize=12)
    ax.set_ylabel("Na$_2$O + K$_2$O (wt%)", color=text_color, fontweight='bold', fontsize=12)
    
    ax.tick_params(colors=text_color, which='both')
    for spine in ax.spines.values():
        spine.set_color(line_color)
        
    fig.tight_layout()
    return fig
