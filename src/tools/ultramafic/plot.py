import matplotlib
import matplotlib.cm as cm
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
from matplotlib.path import Path
import yaml
import os
import numpy as np

def load_classifications():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    yml_path = os.path.join(current_dir, 'classifications.yml')
    with open(yml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def classify_sample(ol, opx, cpx, classifications):
    total = ol + opx + cpx
    if total == 0:
        return "Unknown"
    
    ol_norm = ol / total * 100
    opx_norm = opx / total * 100
    cpx_norm = cpx / total * 100
        
    for class_name, data in classifications.items():
        ol_min, ol_max = data.get('Ol', [0, 100])
        opx_min, opx_max = data.get('Opx', [0, 100])
        cpx_min, cpx_max = data.get('Cpx', [0, 100])
        r_min, r_max = data.get('Cpx_ratio', [0, 100])
        
        eps = 1e-6
        r = (cpx_norm / (opx_norm + cpx_norm)) * 100 if (opx_norm + cpx_norm) > 0 else 50.0
        
        if (ol_min - eps <= ol_norm <= ol_max + eps and 
            opx_min - eps <= opx_norm <= opx_max + eps and 
            cpx_min - eps <= cpx_norm <= cpx_max + eps and
            r_min - eps <= r <= r_max + eps):
            return class_name
            
    return "Unknown"

def plot_ultramafic(normalized_df=None, dark_mode=True):
    classifications = load_classifications()
    
    # Create the figure
    fig = Figure(figsize=(11, 6.5), dpi=100)
    
    # Configure colors based on mode
    bg_color = '#1e1e1e' if dark_mode else '#ffffff'
    text_color = '#e0e0e0' if dark_mode else '#000000'
    grid_color = '#333333' if dark_mode else '#cccccc'
    
    fig.patch.set_facecolor(bg_color)
    
    # Create main axis for the ternary plot
    ax = fig.add_axes([0.15, 0.05, 0.55, 0.90])
    ax.set_facecolor(bg_color)
    
    ax.axis('off')
    
    def to_cartesian(ol, opx, cpx):
        total = ol + opx + cpx
        if total == 0:
            return 0, 0
        ol_n, opx_n, cpx_n = ol/total, opx/total, cpx/total
        
        # opx is at (0, 0)
        # cpx is at (1, 0)
        # ol is at (0.5, sqrt(3)/2)
        x = cpx_n + 0.5 * ol_n
        y = ol_n * np.sqrt(3) / 2.0
        return x * 100, y * 100

    # Draw subtle background grid
    for v in range(10, 100, 10):
        # Constant ol
        p1 = to_cartesian(v, 100-v, 0)
        p2 = to_cartesian(v, 0, 100-v)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=0)
        # Constant opx
        p1 = to_cartesian(100-v, v, 0)
        p2 = to_cartesian(0, v, 100-v)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=0)
        # Constant cpx
        p1 = to_cartesian(100-v, 0, v)
        p2 = to_cartesian(0, 100-v, v)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=0)
        
    
        
    def get_polygon_vertices(bounds):
        ol_min, ol_max = bounds.get('Ol', [0, 100])
        opx_min, opx_max = bounds.get('Opx', [0, 100])
        cpx_min, cpx_max = bounds.get('Cpx', [0, 100])
        r_min, r_max = bounds.get('Cpx_ratio', [0, 100])
        
        pts = []
        def check_pt(ol, opx, cpx):
            eps = 1e-6
            if not (99.9 <= ol + opx + cpx <= 100.1): return
            r = (cpx / (opx + cpx)) * 100 if (opx + cpx) > 0 else 50
            if (ol_min - eps <= ol <= ol_max + eps and 
                opx_min - eps <= opx <= opx_max + eps and 
                cpx_min - eps <= cpx <= cpx_max + eps and
                r_min - eps <= r <= r_max + eps):
                pts.append((ol, opx, cpx))
                
        def intersect(line1, line2):
            def get_ab(line):
                t, val = line
                if t == 'ol': return 1, 0, val
                if t == 'opx': return 1, 1, 100 - val
                if t == 'cpx': return 0, 1, val
                if t == 'r': return val, 100, 100 * val
            
            a1, b1, c1 = get_ab(line1)
            a2, b2, c2 = get_ab(line2)
            det = a1*b2 - a2*b1
            if abs(det) > 1e-9:
                ol = (c1*b2 - c2*b1) / det
                cpx = (a1*c2 - a2*c1) / det
                check_pt(ol, 100 - ol - cpx, cpx)

        lines = [
            ('ol', ol_min), ('ol', ol_max),
            ('opx', opx_min), ('opx', opx_max),
            ('cpx', cpx_min), ('cpx', cpx_max),
            ('r', r_min), ('r', r_max)
        ]
        
        for i in range(len(lines)):
            for j in range(i+1, len(lines)):
                intersect(lines[i], lines[j])
        
        unique_pts = []
        for p in pts:
            if not any(np.allclose(p, up) for up in unique_pts):
                unique_pts.append(p)
                
        cart_coords = [to_cartesian(p[0], p[1], p[2]) for p in unique_pts]
        
        # Sort vertices by angle around centroid
        if len(cart_coords) > 2:
            cx = sum([p[0] for p in cart_coords]) / len(cart_coords)
            cy = sum([p[1] for p in cart_coords]) / len(cart_coords)
            cart_coords = sorted(cart_coords, key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
            
        return cart_coords

    # Replicate the exact colors used in QAPF
    cmap = matplotlib.colormaps.get_cmap('tab20') if hasattr(matplotlib, 'colormaps') else cm.get_cmap('tab20')
    colors = [cmap(i % 20) for i in range(len(classifications))]

    # Draw polygons
    legend_handles = []
    
    for (class_name, data), color in zip(classifications.items(), colors):
        cart_coords = get_polygon_vertices(data)
        
        if len(cart_coords) >= 3:
            poly = mpatches.Polygon(cart_coords, facecolor=color, edgecolor=text_color, linewidth=1, alpha=0.4, zorder=1)
            ax.add_patch(poly)
            
            # Add to legend
            patch = mpatches.Patch(color=color, alpha=0.4, label=class_name)
            legend_handles.append(patch)
        
    # Draw ternary outline and labels
    corners = [to_cartesian(100,0,0), to_cartesian(0,100,0), to_cartesian(0,0,100)]
    outline = mpatches.Polygon(corners, fill=False, edgecolor=text_color, linewidth=2, zorder=2)
    ax.add_patch(outline)
    
    # Labels
    offset = 5
    top = to_cartesian(100,0,0)
    left = to_cartesian(0,100,0)
    right = to_cartesian(0,0,100)
    
    ax.text(top[0], top[1] + offset, 'Ol', ha='center', va='bottom', fontsize=16, color=text_color, fontweight='bold')
    ax.text(left[0] - offset, left[1] - offset, 'Opx', ha='right', va='top', fontsize=16, color=text_color, fontweight='bold')
    ax.text(right[0] + offset, right[1] - offset, 'Cpx', ha='left', va='top', fontsize=16, color=text_color, fontweight='bold')
    
    ax.set_xlim(-5, 105)
    ax.set_ylim(-15, 95)
    ax.set_aspect('equal', adjustable='box')
    
    # Draw legend exactly like Feldspar
    if legend_handles:
        ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1.05, 0.5), 
                  frameon=False, fontsize=10, labelcolor=text_color)
    
    # Plot samples
    if normalized_df is not None and not normalized_df.empty:
        x_cart = []
        y_cart = []
        for _, row in normalized_df.iterrows():
            ol, opx, cpx = row['Ol'], row['Opx'], row['Cpx']
            cx, cy = to_cartesian(ol, opx, cpx)
            x_cart.append(cx)
            y_cart.append(cy)
            
        ax.scatter(x_cart, y_cart, color='orange', s=100, edgecolors='black', linewidths=1, zorder=3, alpha=1.0)
    return fig
