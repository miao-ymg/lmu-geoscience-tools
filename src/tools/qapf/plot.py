import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import yaml
import matplotlib.patches as patches
from theme import colors
from tools.common.plot_utils import draw_sample_points, draw_classifications_legend

def _get_resource_path(filename):
    """Get absolute path to a resource file in the qapf package.
    Works both in normal Python execution and inside a PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle: files are extracted to sys._MEIPASS/tools/qapf/
        return os.path.join(sys._MEIPASS, 'tools', 'qapf', filename)
    else:
        # Normal execution: files are next to this script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def get_classifications():
    yaml_path = _get_resource_path('classifications.yml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def draw_grid(ax, default_color, default_alpha, accent_color, highlight_axis=None, mode='QAPF'):
    sqrt3_2 = np.sqrt(3) / 2
    for v in range(10, 100, 10):
        # By default, use neutral grey
        q_color, q_alpha = default_color, default_alpha
        a_color, a_alpha = default_color, default_alpha
        p_color, p_alpha = default_color, default_alpha
        f_color, f_alpha = default_color, default_alpha
        
        # Default line width matches draw_ternary_grid
        q_lw = a_lw = p_lw = f_lw = 0.5
        
        # The higher the value v, the higher the opacity for the highlighted axis
        # We map v=10 to alpha=0.2 and v=90 to alpha=1.0 to make it super clear
        highlight_alpha = (v / 100) * 0.9 + 0.1 
        highlight_lw = 1.5 

        if highlight_axis == 'Q':
            q_color = accent_color
            q_alpha = highlight_alpha
            q_lw = highlight_lw
        elif highlight_axis == 'A':
            a_color = accent_color
            a_alpha = highlight_alpha
            a_lw = highlight_lw
        elif highlight_axis == 'P':
            p_color = accent_color
            p_alpha = highlight_alpha
            p_lw = highlight_lw
        elif highlight_axis == 'F':
            f_color = accent_color
            f_alpha = highlight_alpha
            f_lw = highlight_lw

        # QAP lines
        if mode in ['QAPF', 'QAP']:
            # Horizontal (constant Q)
            ax.plot([-(100-v)/2, (100-v)/2], [v*sqrt3_2, v*sqrt3_2], color=q_color, alpha=q_alpha, lw=q_lw, zorder=1)
            # Constant A
            ax.plot([-v/2, 50 - v], [(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=a_lw, zorder=1)
            # Constant P
            ax.plot([v/2, v - 50], [(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=p_lw, zorder=1)
        
        # APF lines
        if mode in ['QAPF', 'APF']:
            if mode == 'APF':
                # F points UP. Exact same geometry as QAP!
                # Horizontal (constant F)
                ax.plot([-(100-v)/2, (100-v)/2], [v*sqrt3_2, v*sqrt3_2], color=f_color, alpha=f_alpha, lw=f_lw, zorder=1)
                # Constant A
                ax.plot([-v/2, 50 - v], [(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=a_lw, zorder=1)
                # Constant P
                ax.plot([v/2, v - 50], [(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=p_lw, zorder=1)
            else:
                # F points DOWN (QAPF mode)
                # Horizontal (constant F)
                ax.plot([-(100-v)/2, (100-v)/2], [-v*sqrt3_2, -v*sqrt3_2], color=f_color, alpha=f_alpha, lw=f_lw, zorder=1)
                # Constant A
                ax.plot([-v/2, 50 - v], [-(100-v)*sqrt3_2, 0], color=a_color, alpha=a_alpha, lw=a_lw, zorder=1)
                # Constant P
                ax.plot([v/2, v - 50], [-(100-v)*sqrt3_2, 0], color=p_color, alpha=p_alpha, lw=p_lw, zorder=1)

def plot_qapf(normalized_df, mode='QAPF', dark_mode=False, highlight_axis=None, classification=None):
    """
    Plots a QAPF diagram.
    Returns a matplotlib Figure object.
    """
    if dark_mode:
        bg_color = colors['plot-bg-dark']
        line_color = colors['plot-line-dark']
        text_color = colors['plot-text-dark']
        grid_color = colors['plot-grid-dark']
        grid_alpha = 1.0
        
        point_color = colors['plot-point-dark']
        edge_color = colors['plot-edge-dark']
        accent_color = colors['plot-accent-dark']
    else:
        bg_color = colors['plot-bg-light']
        line_color = colors['plot-line-light']
        text_color = colors['plot-text-light']
        grid_color = colors['plot-grid-light']
        grid_alpha = 0.5
        
        point_color = colors['plot-point-light']
        edge_color = colors['plot-edge-light']
        accent_color = colors['plot-accent-light']

    has_right_panel = (classification and classification != 'None')
    
    # Increase width to make room for legend in the right panel
    fig_width = 11 if has_right_panel else 8
    fig_height = 8 if mode == 'QAPF' else 6.5
    fig = plt.figure(figsize=(fig_width, fig_height), facecolor=bg_color)
    
    if mode == 'QAPF':
        if has_right_panel:
            ax = fig.add_axes([0.02, 0.18, 0.50, 0.80])
        else:
            ax = fig.add_axes([0.15, 0.18, 0.70, 0.80])
    else:
        # Single triangle mode matches QAPF bottom padding for consistent colorbar
        if has_right_panel:
            ax = fig.add_axes([0.15, 0.15, 0.55, 0.80])
        else:
            ax = fig.add_axes([0.15, 0.15, 0.70, 0.80])
        
    ax.set_facecolor(bg_color)
    
    sqrt3_2 = np.sqrt(3) / 2
    
    # Vertices
    Q = (0, 100 * sqrt3_2)
    A = (-50, 0)
    P = (50, 0)
    F = (0, -100 * sqrt3_2)
    
    if mode == 'APF':
        F = (0, 100 * sqrt3_2)
    
    # Draw internal grid lines BEFORE polygons so they sit in the background
    if highlight_axis:
        draw_grid(ax, default_color=grid_color, default_alpha=grid_alpha, 
                  accent_color=accent_color, highlight_axis=highlight_axis, mode=mode)
    else:
        from tools.common.plot_utils import draw_ternary_grid
        if mode in ['QAPF', 'QAP']:
            draw_ternary_grid(ax, grid_color, scale=1.0, vertices=(np.array(A), np.array(P), np.array(Q)))
        if mode in ['QAPF', 'APF']:
            draw_ternary_grid(ax, grid_color, scale=1.0, vertices=(np.array(A), np.array(P), np.array(F)))
            
    # Draw classification polygons
    if classification and classification != 'None':
        all_classifications = get_classifications()
        if classification in all_classifications:
            class_dict = all_classifications[classification]
            
            # Get a colormap for the classes
            try:
                cmap = plt.colormaps.get_cmap('tab20')
            except AttributeError:
                import matplotlib.cm as cm
                cmap = cm.get_cmap('tab20')
                
            class_colors = [cmap(i % 20) for i in range(len(class_dict))]
            legend_handles = []
            
            for (name, data), color in zip(class_dict.items(), class_colors):
                c_type = 'QAP' if 'Q' in data else 'APF'
                if mode == 'QAP' and c_type != 'QAP': continue
                if mode == 'APF' and c_type != 'APF': continue
                
                p_min, p_max = data.get('P_ratio', [0, 100])
                p_min /= 100.0
                p_max /= 100.0
                
                if c_type == 'QAP':
                    q_min, q_max = data.get('Q', [0, 100])
                    v1 = ((100 - q_min) * (p_min - 0.5), q_min * sqrt3_2)
                    v2 = ((100 - q_min) * (p_max - 0.5), q_min * sqrt3_2)
                    v3 = ((100 - q_max) * (p_max - 0.5), q_max * sqrt3_2)
                    v4 = ((100 - q_max) * (p_min - 0.5), q_max * sqrt3_2)
                else:
                    f_min, f_max = data.get('F', [0, 100])
                    y_sign = 1 if mode == 'APF' else -1
                    v1 = ((100 - f_min) * (p_min - 0.5), y_sign * f_min * sqrt3_2)
                    v2 = ((100 - f_min) * (p_max - 0.5), y_sign * f_min * sqrt3_2)
                    v3 = ((100 - f_max) * (p_max - 0.5), y_sign * f_max * sqrt3_2)
                    v4 = ((100 - f_max) * (p_min - 0.5), y_sign * f_max * sqrt3_2)
                    
                poly = patches.Polygon([v1, v2, v3, v4], facecolor=color, edgecolor=line_color, alpha=0.4, zorder=2)
                ax.add_patch(poly)
                
                patch = patches.Patch(color=color, alpha=0.4, label=name)
                legend_handles.append(patch)
            
            if legend_handles:
                draw_classifications_legend(ax, legend_handles, text_color, ncols=2 if mode == 'QAPF' else 1)
    

    # Draw the outline of the two triangles
    from tools.common.plot_utils import draw_ternary_outline
    
    if mode == 'QAPF':
        # Q-A-P-Q
        ax.plot([Q[0], A[0], P[0], Q[0]], [Q[1], A[1], P[1], Q[1]], color=line_color, lw=2, zorder=3)
        # A-F-P-A
        ax.plot([A[0], F[0], P[0], A[0]], [A[1], F[1], P[1], A[1]], color=line_color, lw=2, zorder=3)
    elif mode == 'QAP':
        draw_ternary_outline(ax, labels=['A', 'P', 'Q'], text_color=text_color, line_color=line_color, scale=100.0, vertices=(np.array(A), np.array(P), np.array(Q)))
    elif mode == 'APF':
        draw_ternary_outline(ax, labels=['A', 'P', 'F'], text_color=text_color, line_color=line_color, scale=100.0, vertices=(np.array(A), np.array(P), np.array(F)))
    
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
        
    draw_sample_points(ax, x_coords, y_coords, point_color=point_color, edge_color=edge_color)
    
    # Add text labels at the corners (only for QAPF double diagram, singles use draw_ternary_outline)
    if mode == 'QAPF':
        ax.text(Q[0], Q[1] + 12, "Q", fontsize=16, ha='center', va='center', fontweight='bold', color=text_color)
        ax.text(A[0] - 8, A[1], "A", fontsize=16, ha='right', va='center', fontweight='bold', color=text_color)
        ax.text(P[0] + 8, P[1], "P", fontsize=16, ha='left', va='center', fontweight='bold', color=text_color)
        ax.text(F[0], F[1] - 12, "F", fontsize=16, ha='center', va='center', fontweight='bold', color=text_color)
    
    # Make sure we can see the labels
    if mode == 'QAP' or mode == 'APF':
        # Match standard ternary bounds for scale=100
        pad_x = 5
        pad_y_bottom = 20
        pad_y_top = 5
        ax.set_xlim(-50 - pad_x, 50 + pad_x)
        if mode == 'QAP':
            ax.set_ylim(-pad_y_bottom, 100 * sqrt3_2 + pad_y_top)
        else: # APF single triangle is drawn pointing UP now!
            ax.set_ylim(-pad_y_bottom, 100 * sqrt3_2 + pad_y_top)
    else:
        ax.set_xlim(-65, 65)
        ax.set_ylim(-105, 105)
    
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
        # Position colorbar under the main triangle, centered
        if mode == 'QAPF':
            ax_x = 0.02 if has_right_panel else 0.15
            ax_w = 0.50 if has_right_panel else 0.70
            cbar_y = 0.11
        else:
            ax_x = 0.15
            ax_w = 0.55 if has_right_panel else 0.70
            cbar_y = 0.11
            
        # Center a 0.5 wide colorbar under the axes
        cbar_w = 0.5
        cbar_x = ax_x + (ax_w - cbar_w) / 2
        
        cbar_ax = fig.add_axes([cbar_x, cbar_y, cbar_w, 0.03])
        cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
        cbar.set_label(f'{highlight_axis} Axis Highlight (%)', color=text_color, fontweight='bold', labelpad=5)
        cbar.ax.xaxis.set_tick_params(color=text_color, labelcolor=text_color)
        cbar.outline.set_edgecolor(text_color)
        
    return fig
