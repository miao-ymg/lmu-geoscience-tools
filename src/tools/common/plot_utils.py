import numpy as np

def get_ternary_vertices(scale=1.0):
    """
    Returns the 2D cartesian coordinates of a standard equilateral triangle
    with side length `scale`.
    Returns: left, right, top
    """
    left = np.array([0.0, 0.0])
    right = np.array([scale, 0.0])
    top = np.array([scale * 0.5, scale * np.sqrt(3) / 2.0])
    return left, right, top

def setup_ternary_bounds(ax, scale=1.0):
    """Sets standard limits and equal aspect ratio for a ternary plot."""
    pad_x = 0.05 * scale
    pad_y_bottom = 0.20 * scale
    pad_y_top = 0.05 * scale
    
    ax.set_xlim(-pad_x, scale + pad_x)
    ax.set_ylim(-pad_y_bottom, (scale * np.sqrt(3) / 2.0) + pad_y_top)
    ax.set_aspect('equal', adjustable='box')

def draw_ternary_outline(ax, labels, text_color, line_color, scale=1.0, vertices=None):
    """
    Draws the outer equilateral triangle and corner labels.
    labels: [left_label, right_label, top_label]
    """
    import matplotlib.pyplot as plt
    
    if vertices:
        left, right, top = vertices
    else:
        left, right, top = get_ternary_vertices(scale)
    
    triangle = plt.Polygon(
        [left, right, top],
        closed=True,
        fill=False,
        edgecolor=line_color,
        linewidth=2,
        zorder=3
    )
    ax.add_patch(triangle)
    
    offset = 0.05 * scale
    
    def _draw_label(x, y, label, ha):
        if isinstance(label, tuple):
            main_t, sub_t = label
            # Vertically center the two lines around y
            ax.text(x, y + 0.02 * scale, main_t, ha=ha, va='center', fontsize=16, color=text_color, fontweight='bold')
            ax.text(x, y - 0.02 * scale, sub_t, ha=ha, va='center', fontsize=11, color=text_color)
        else:
            # Vertically center single line at y
            ax.text(x, y, label, ha=ha, va='center', fontsize=16, color=text_color, fontweight='bold')
            
    # Left corner
    _draw_label(left[0] - offset, left[1] - offset, labels[0], 'right')
    
    # Right corner
    _draw_label(right[0] + offset, right[1] - offset, labels[1], 'left')
            
    # Top corner
    _draw_label(top[0], top[1] + offset, labels[2], 'center')

def draw_ternary_grid(ax, grid_color, scale=1.0, vertices=None):
    """Draws 10% interval background grid lines."""
    if vertices:
        left, right, top = vertices
    else:
        left, right, top = get_ternary_vertices(scale)
    
    for v in range(10, 100, 10):
        frac = v / 100.0
        
        # Constant Left
        p1 = left + frac * (right - left)
        p2 = left + frac * (top - left)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)
        
        # Constant Right
        p1 = right + frac * (left - right)
        p2 = right + frac * (top - right)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)
        
        # Constant Top
        p1 = top + frac * (left - top)
        p2 = top + frac * (right - top)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)

def draw_classifications_legend(ax, handles, text_color, ncols=1):
    """Standardized side-legend for colored classification plots."""
    if handles:
        ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.15, 0.5), 
                  frameon=False, fontsize=9, labelcolor=text_color, ncol=ncols)

def draw_sample_points(ax, xs, ys, point_color='orange', edge_color='black'):
    """Standardized scatter plot styling for samples."""
    ax.scatter(xs, ys, color=point_color, s=100, edgecolors=edge_color, 
               linewidths=1.5, zorder=5, alpha=1.0, marker='o')
