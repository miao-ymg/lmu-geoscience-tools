import matplotlib
import matplotlib.cm as cm
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.path import Path
import yaml
import os
import numpy as np

from tools.common.plot_utils import (
    setup_ternary_bounds, draw_ternary_outline, draw_ternary_grid,
    draw_classifications_legend, draw_sample_points
)

import sys

def _get_resource_path(filename):
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tools', 'ultramafic', filename)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def load_classifications():
    yml_path = _get_resource_path('classifications.yml')
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
    setup_ternary_bounds(ax, scale=100.0)
    
    def to_cartesian(ol, opx, cpx):
        total = ol + opx + cpx
        if total == 0:
            return 0, 0
        ol_n, opx_n, cpx_n = ol/total, opx/total, cpx/total
        x = cpx_n + 0.5 * ol_n
        y = ol_n * np.sqrt(3) / 2.0
        return x * 100, y * 100

    # Draw subtle background grid
    draw_ternary_grid(ax, grid_color, scale=100.0)
        
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
    draw_ternary_outline(
        ax, 
        labels=['Opx', 'Cpx', 'Ol'], 
        text_color=text_color, 
        line_color=text_color, 
        scale=100.0
    )
    
    # Draw legend exactly like Feldspar
    draw_classifications_legend(ax, legend_handles, text_color)
    
    # Plot samples
    if normalized_df is not None and not normalized_df.empty:
        x_cart = []
        y_cart = []
        for _, row in normalized_df.iterrows():
            ol, opx, cpx = row['Ol'], row['Opx'], row['Cpx']
            cx, cy = to_cartesian(ol, opx, cpx)
            x_cart.append(cx)
            y_cart.append(cy)
            
        draw_sample_points(ax, x_cart, y_cart, point_color='orange', edge_color='black')
        
    return fig
