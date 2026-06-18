import matplotlib.pyplot as plt
import numpy as np

def draw_grid(ax, default_color, default_alpha, accent_color, highlight_axis=None, mode='QAPF'):
    sqrt3_2 = np.sqrt(3) / 2
    for v in range(10, 100, 10):
        # By default, use neutral grey
        q_color, q_alpha = default_color, default_alpha
        a_color, a_alpha = default_color, default_alpha
        p_color, p_alpha = default_color, default_alpha
        f_color, f_alpha = default_color, default_alpha
        
        # Base line width for everything
        lw = 1.0
        
        # The higher the value v, the higher the opacity for the highlighted axis
        # We map v=10 to alpha=0.2 and v=90 to alpha=1.0 to make it super clear
        highlight_alpha = (v / 100) * 0.9 + 0.1 

        if highlight_axis == 'Q':
            q_color = accent_color
            q_alpha = highlight_alpha
        elif highlight_axis == 'A':
            a_color = accent_color
            a_alpha = highlight_alpha
        elif highlight_axis == 'P':
            p_color = accent_color
            p_alpha = highlight_alpha
        elif highlight_axis == 'F':
            f_color = accent_color
            f_alpha = highlight_alpha

        # QAP lines
        if mode in ['QAPF', 'QAP']:
            # Horizontal (constant Q)
            ax.plot([-(100-v)/2, (100-v)/2], [v*sqrt3_2, v*sqrt3_2], color=q_color, alpha=q_alpha, lw=lw, zorder=1)
            # Constant A
            ax.plot([-v/2, 50 - v], [(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=lw, zorder=1)
            # Constant P
            ax.plot([v/2, v - 50], [(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=lw, zorder=1)
        
        # APF lines
        if mode in ['QAPF', 'APF']:
            if mode == 'APF':
                # F points UP. Exact same geometry as QAP!
                # Horizontal (constant F)
                ax.plot([-(100-v)/2, (100-v)/2], [v*sqrt3_2, v*sqrt3_2], color=f_color, alpha=f_alpha, lw=lw, zorder=1)
                # Constant A
                ax.plot([-v/2, 50 - v], [(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=lw, zorder=1)
                # Constant P
                ax.plot([v/2, v - 50], [(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=lw, zorder=1)
            else:
                # F points DOWN (QAPF mode)
                # Horizontal (constant F)
                ax.plot([-(100-v)/2, (100-v)/2], [-v*sqrt3_2, -v*sqrt3_2], color=f_color, alpha=f_alpha, lw=lw, zorder=1)
                # Constant A
                ax.plot([-v/2, 50 - v], [-(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=lw, zorder=1)
                # Constant P
                ax.plot([v/2, v - 50], [-(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=lw, zorder=1)

def plot_qapf(normalized_df, mode='QAPF', dark_mode=False, highlight_axis=None):
    """
    Plots a QAPF diagram.
    Returns a matplotlib Figure object.
    """
    if dark_mode:
        bg_color = '#1e1e1e' # Pure neutral dark grey
        line_color = '#e0e0e0'
        text_color = '#e0e0e0'
        grid_color = '#333333'
        grid_alpha = 1.0
        point_color = '#ff4d4d' 
        edge_color = '#1e1e1e'
        accent_color = '#a6e3a1' # Green
    else:
        bg_color = 'white'
        line_color = 'black'
        text_color = 'black'
        grid_color = '#dddddd'
        grid_alpha = 1.0
        point_color = '#ff4d4d'
        edge_color = 'black'
        accent_color = '#40a02b' # Darker green for light mode visibility

    fig = plt.figure(figsize=(8, 8), facecolor=bg_color)
    # Explicitly position the main axes so its size NEVER changes
    ax = fig.add_axes([0.1, 0.20, 0.8, 0.75])
    ax.set_facecolor(bg_color)
    
    sqrt3_2 = np.sqrt(3) / 2
    
    # Vertices
    Q = (0, 100 * sqrt3_2)
    A = (-50, 0)
    P = (50, 0)
    F = (0, -100 * sqrt3_2)
    
    if mode == 'APF':
        F = (0, 100 * sqrt3_2)
    
    # Draw internal grid lines
    draw_grid(ax, default_color=grid_color, default_alpha=grid_alpha, 
              accent_color=accent_color, highlight_axis=highlight_axis, mode=mode)
    
    # Draw the outline of the two triangles
    if mode in ['QAPF', 'QAP']:
        # Q-A-P-Q
        ax.plot([Q[0], A[0], P[0], Q[0]], [Q[1], A[1], P[1], Q[1]], color=line_color, lw=1.5, zorder=2)
    if mode in ['QAPF', 'APF']:
        # A-F-P-A
        ax.plot([A[0], F[0], P[0], A[0]], [A[1], F[1], P[1], A[1]], color=line_color, lw=1.5, zorder=2)
    
    # Plot points
    x_coords = []
    y_coords = []
    
    for _, row in normalized_df.iterrows():
        p_ratio = row.get('P_ratio', 0.5)
        
        if row['type'] == 'QAP':
            q = row.get('Q', 0)
            y = q * sqrt3_2
            x = (100 - q) * (p_ratio - 0.5)
        else:
            f = row.get('F', 0)
            if mode == 'APF':
                y = f * sqrt3_2
                x = (100 - f) * (p_ratio - 0.5)
            else:
                y = -f * sqrt3_2
                x = (100 - f) * (p_ratio - 0.5)
            
        x_coords.append(x)
        y_coords.append(y)
        
    ax.scatter(x_coords, y_coords, color=point_color, s=50, edgecolors=edge_color, zorder=5)
    
    # Add text labels at the corners
    if mode in ['QAPF', 'QAP']:
        ax.text(Q[0], Q[1] + 5, "Q", fontsize=14, ha='center', fontweight='bold', color=text_color)
    ax.text(A[0] - 5, A[1], "A", fontsize=14, ha='right', va='center', fontweight='bold', color=text_color)
    ax.text(P[0] + 5, P[1], "P", fontsize=14, ha='left', va='center', fontweight='bold', color=text_color)
    if mode in ['QAPF', 'APF']:
        if mode == 'APF':
            ax.text(F[0], F[1] + 5, "F", fontsize=14, ha='center', va='bottom', fontweight='bold', color=text_color)
        else:
            ax.text(F[0], F[1] - 5, "F", fontsize=14, ha='center', va='top', fontweight='bold', color=text_color)
    
    # Make sure we can see the labels
    ax.set_xlim(-70, 70)
    if mode == 'QAP' or mode == 'APF':
        ax.set_ylim(-10 * sqrt3_2, 110 * sqrt3_2)
    else:
        ax.set_ylim(-110 * sqrt3_2, 110 * sqrt3_2)
    
    ax.set_aspect('equal')
    ax.axis('off')  # Hide grid and axes
    
    from matplotlib.colors import LinearSegmentedColormap
    import matplotlib.colors as mcolors
    
    # We blend the background color to the accent color for the legend
    bg_rgb = mcolors.to_rgb(bg_color)
    accent_rgb = mcolors.to_rgb(accent_color)
    cmap = LinearSegmentedColormap.from_list('alpha_blend', [bg_rgb, accent_rgb])
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0, vmax=100))
    
    if highlight_axis in ['Q', 'A', 'P', 'F']:
        # Explicitly position the colorbar axes at the bottom so it never steals space from main ax
        cbar_ax = fig.add_axes([0.15, 0.08, 0.7, 0.03])
        cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
        cbar.set_label(f'{highlight_axis} Axis Highlight (%)', color=text_color, fontweight='bold', labelpad=5)
        cbar.ax.xaxis.set_tick_params(color=text_color, labelcolor=text_color)
        cbar.outline.set_edgecolor(text_color)
        
    return fig
