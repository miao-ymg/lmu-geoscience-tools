import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import os
import sys
import yaml

def _get_resource_path(filename):
    """Get absolute path to a resource file in the feldspar package.
    Works both in normal Python execution and inside a PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        return os.path.join(sys._MEIPASS, 'tools', 'feldspar', filename)
    else:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def get_classifications():
    yaml_path = _get_resource_path('classifications.yml')
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def _ternary_coords(ab, or_, an):
    """
    Convert ternary (Ab, Or, An) fractions to 2-D Cartesian coordinates
    for plotting inside a standard equilateral triangle.

    Convention (counter-clockwise vertices):
      bottom-left  = Ab  (Albite)
      bottom-right = An  (Anorthite)
      top          = Or  (Orthoclase)
    """
    x = an + 0.5 * or_
    y = or_ * np.sqrt(3) / 2
    return x, y


def plot_feldspar(endmembers_df: pd.DataFrame, dark_mode: bool = True) -> plt.Figure:
    """
    Generates a ternary feldspar diagram with columns Ab, Or, An.

    Vertices (counter-clockwise):
      bottom-left  = Ab
      bottom-right = An
      top          = Or

    Returns a matplotlib Figure.
    """
    if dark_mode:
        bg_color    = '#1e1e1e'
        text_color  = '#e0e0e0'
        line_color  = '#e0e0e0'
        grid_color  = '#333333'
        point_color = 'orange'
        edge_color  = '#1e1e1e'
    else:
        bg_color    = 'white'
        text_color  = 'black'
        line_color  = 'black'
        grid_color  = '#dddddd'
        point_color = 'orange'
        edge_color  = 'black'

    # Read classifications
    all_classifications = get_classifications()
    class_dict = all_classifications.get('Default', {})

    # Increase width to make room for legend
    fig_width = 11 if class_dict else 8
    fig = plt.figure(figsize=(fig_width, 6.5), facecolor=bg_color)
    
    if class_dict:
        # Center the combined bounding box of (triangle + legend)
        # Shifted right from 0.05 to 0.15, bottom margin reduced to 0.05
        ax = fig.add_axes([0.15, 0.05, 0.55, 0.90])
    else:
        ax = fig.add_axes([0.1, 0.05, 0.8, 0.90])
        
    ax.set_facecolor(bg_color)
    # Set up the plot correctly centered
    ax.set_aspect('equal', adjustable='box')
    ax.axis('off')
    ax.set_xlim(-0.05, 1.05)
    # Expand bottom limit to ensure chemical formulas are not cut off
    ax.set_ylim(-0.15, 0.95)

    # ── Triangle outline ───────────────────────────────────────────────
    # Vertices in 2-D:  Ab=(0,0), An=(1,0), Or=(0.5, sqrt(3)/2)
    V_Ab = np.array([0.0, 0.0])
    V_An = np.array([1.0, 0.0])
    V_Or = np.array([0.5, np.sqrt(3) / 2])

    triangle = plt.Polygon(
        [V_Ab, V_An, V_Or],
        closed=True,
        fill=False,
        edgecolor=line_color,
        linewidth=2,
    )
    ax.add_patch(triangle)

    # ── Grid lines (every 10 %) ────────────────────────────────────────
    for v in range(10, 100, 10):
        frac = v / 100.0

        # Constant Ab = frac: moves along Ab-An and Ab-Or
        p1 = V_Ab + frac * (V_An - V_Ab)
        p2 = V_Ab + frac * (V_Or - V_Ab)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)

        # Constant An = frac
        p1 = V_An + frac * (V_Ab - V_An)
        p2 = V_An + frac * (V_Or - V_An)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)

        # Constant Or = frac
        p1 = V_Or + frac * (V_Ab - V_Or)
        p2 = V_Or + frac * (V_An - V_Or)
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color=grid_color, linewidth=0.5, zorder=1)

    # ── Classifications Overlay ───────────────────────────────────────
    # Read classifications
    all_classifications = get_classifications()
    class_dict = all_classifications.get('Default', {})
    
    import math

    def _get_region_polygon(rules):
        if 'polygon' in rules:
            pts = [(p['An']/100.0, p['Or']/100.0) for p in rules['polygon']]
            return [(1.0 - p[0] - p[1], p[1], p[0]) for p in pts]
            
        ineqs = []
        ineqs.append((1, 0, 0))
        ineqs.append((0, 1, 0))
        ineqs.append((-1, -1, 1))
        
        if 'An' in rules:
            cmin, cmax = [x / 100.0 for x in rules['An']]
            ineqs.append((1, 0, -cmin))
            ineqs.append((-1, 0, cmax))
        if 'Or' in rules:
            cmin, cmax = [x / 100.0 for x in rules['Or']]
            ineqs.append((0, 1, -cmin))
            ineqs.append((0, -1, cmax))
        if 'An_ratio' in rules:
            cmin, cmax = [x / 100.0 for x in rules['An_ratio']]
            ineqs.append((1, cmin, -cmin))
            ineqs.append((-1, -cmax, cmax))
        if 'Or_ratio' in rules:
            cmin, cmax = [x / 100.0 for x in rules['Or_ratio']]
            ineqs.append((cmin, 1, -cmin))
            ineqs.append((-cmax, -1, cmax))
        if 'Ab_ratio' in rules:
            cmin, cmax = [x / 100.0 for x in rules['Ab_ratio']]
            ineqs.append((-cmin, 1 - cmin, 0))
            ineqs.append((cmax, cmax - 1, 0))
        if 'Or_perp' in rules:
            cmin, cmax = [x / 100.0 for x in rules['Or_perp']]
            ineqs.append((1, 2, -2*cmin))
            ineqs.append((-1, -2, 2*cmax))
            
        pts = []
        n = len(ineqs)
        for i in range(n):
            for j in range(i + 1, n):
                A1, B1, C1 = ineqs[i]
                A2, B2, C2 = ineqs[j]
                det = A1 * B2 - A2 * B1
                if abs(det) > 1e-9:
                    an = (B1 * C2 - B2 * C1) / det
                    or_ = (A2 * C1 - A1 * C2) / det
                    valid = True
                    for A, B, C in ineqs:
                        if A * an + B * or_ + C < -1e-6:
                            valid = False
                            break
                    if valid:
                        pts.append((an, or_))
                        
        if not pts:
            return []
            
        unique_pts = []
        for p in pts:
            if not any(abs(p[0]-up[0]) < 1e-5 and abs(p[1]-up[1]) < 1e-5 for up in unique_pts):
                unique_pts.append(p)
                
        if len(unique_pts) < 3:
            return []
            
        cent_an = sum(p[0] for p in unique_pts) / len(unique_pts)
        cent_or = sum(p[1] for p in unique_pts) / len(unique_pts)
        unique_pts.sort(key=lambda p: math.atan2(p[1] - cent_or, p[0] - cent_an))
        
        return [(1.0 - p[0] - p[1], p[1], p[0]) for p in unique_pts]

    # Use the EXACT same color palette as QAPF
    try:
        cmap = plt.colormaps.get_cmap('tab20')
    except AttributeError:
        import matplotlib.cm as cm
        cmap = cm.get_cmap('tab20')
        
    region_colors = [cmap(i % 20) for i in range(20)]
    legend_handles = []
    
    # We want a stable color map for names so duplicates get the same color
    name_colors = {}
    color_idx = 0
    for class_rule in class_dict:
        name = class_rule['name']
        if name not in name_colors and name != "Miscibility Gap":
            name_colors[name] = region_colors[color_idx % len(region_colors)]
            color_idx += 1
            
    # Track drawn labels to avoid duplicate legend entries/text
    drawn_labels = set()

    for class_rule in class_dict:
        class_name = class_rule['name']
            
        ternary_pts = _get_region_polygon(class_rule)
        if ternary_pts:
            poly_coords = [_ternary_coords(ab, or_, an) for ab, or_, an in ternary_pts]
            
            if class_name == "Miscibility Gap":
                color = bg_color
                z = 3  # Draw over other regions
                alpha = 1.0
                edge_col = line_color
            else:
                color = name_colors[class_name]
                z = 1
                alpha = 0.4
                edge_col = line_color
            
            p = plt.Polygon(poly_coords, closed=True, fill=True, facecolor=color, 
                            edgecolor=edge_col, linewidth=1.0, alpha=alpha, zorder=z)
            ax.add_patch(p)
            
            if class_name != "Miscibility Gap" and class_name not in drawn_labels:
                # Add to legend
                patch = mpatches.Patch(facecolor=color, edgecolor=line_color, linewidth=1.0, alpha=0.4, label=class_name)
                legend_handles.append(patch)
                drawn_labels.add(class_name)
            
            # Add label text in center of polygon
            if class_name != "Miscibility Gap" and 'polygon' not in class_rule:
                if 'label_pos' in class_rule:
                    lp = class_rule['label_pos']
                    # Calculate Ab based on An and Or
                    ab_val = 100.0 - lp['An'] - lp['Or']
                    center_x, center_y = _ternary_coords(ab_val/100.0, lp['Or']/100.0, lp['An']/100.0)
                else:
                    center_x = sum(c[0] for c in poly_coords) / len(poly_coords)
                    center_y = sum(c[1] for c in poly_coords) / len(poly_coords)
                
                ax.text(center_x, center_y, class_name, color=text_color, fontsize=7, ha='center', va='center', zorder=5)

    label_offset = 0.06
    sqrt3_2 = np.sqrt(3) / 2
            
    # Ab (bottom-left)
    ax.text(0, -label_offset, "Ab", color=text_color, fontsize=14, ha='center', va='top', fontweight='bold')
    ax.text(0, -label_offset - 0.05, "NaAlSi$_3$O$_8$", color=text_color, fontsize=10, ha='center', va='top')
    
    # An (bottom-right)
    ax.text(1, -label_offset, "An", color=text_color, fontsize=14, ha='center', va='top', fontweight='bold')
    ax.text(1, -label_offset - 0.05, "CaAl$_2$Si$_2$O$_8$", color=text_color, fontsize=10, ha='center', va='top')
    
    # Or (top)
    ax.text(0.5, sqrt3_2 + label_offset, "Or", color=text_color, fontsize=14, ha='center', va='bottom', fontweight='bold')
    ax.text(0.5, sqrt3_2 + label_offset - 0.04, "KAlSi$_3$O$_8$", color=text_color, fontsize=10, ha='center', va='bottom')

    # Edge texts
    # Ab-Or edge
    ax.text(0.20, sqrt3_2/2 + 0.05, "Alkali Feldspars", color=text_color, fontsize=12, ha='center', va='center', rotation=60)
    # Ab-An edge
    ax.text(0.5, -0.05, "Plagioclases", color=text_color, fontsize=12, ha='center', va='top')

    # ── Data points ───────────────────────────────────────────────────
    if not endmembers_df.empty:
        xs, ys = [], []
        for _, row in endmembers_df.iterrows():
            x, y = _ternary_coords(row['Ab'], row['Or'], row['An'])
            xs.append(x)
            ys.append(y)

        ax.scatter(xs, ys, color=point_color, s=100, edgecolors=edge_color, zorder=6, marker='o')

    if legend_handles:
        ax.legend(handles=legend_handles, loc='center left', bbox_to_anchor=(1.05, 0.5), 
                  frameon=False, fontsize=10, labelcolor=text_color)

    return fig
