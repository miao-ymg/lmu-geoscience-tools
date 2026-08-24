"""
Centralized color palette for the LMU Geoscience Tools.
All hex codes must use lowercase letters.
"""

COLORS = {
    # UI Text
    "@text-main": "#f0f3f6",
    "@text-serif": "#f0f3f6",
    "@text-sub": "#788390",
    "@text-dim": "#717d8a",
    "@text-green": "#52795d",
    "@accent-green": "#4d7a58",
    "@text-white": "#ffffff",
    "@text-accent": "#90c527",
    "@text-accent-hover": "#9ef04d",
    "@text-sidebar-header": "#5d6e7f",
    "@text-instruction-note": "#8c9baa",
    "@text-link": "#627284",
    "@text-upload-subtitle": "#788796",
    "@text-instruction-header": "#cad3df",
    "@text-btn-generate": "#0b1008",
    "@text-btn-disabled": "#435b44",
    "@text-warning": "#d19a66",

    # UI Backgrounds
    "@bg-base": "#161b22",
    "@bg-mantle": "#0d1117",
    "@bg-hover": "#1b222d",
    "@bg-active": "#223026",
    "@bg-upload": "#1c212b",
    "@bg-upload-hover": "#222834",
    "@bg-upload-icon": "#232f22",
    "@bg-btn-disabled": "#182218",

    # UI Borders
    "@border-active": "#3e5a42",
    "@border-dark": "#21262d",
    "@border-subtle": "#30363d",
    "@border-upload": "#4e7330",
    "@border-upload-hover": "#72a34f",
    "@border-instructions": "#28313e",
    "@border-note": "#1a2330",
    "@border-btn-disabled": "#223323",

    # UI Toggles
    "@toggle-bg": "#1a222c",
    "@toggle-border": "#273140",
    "@toggle-bg-hover": "#232d3b",
    "@toggle-bg-checked": "#26382b",
    "@toggle-text-checked": "#c9e8cd",
    "@toggle-border-checked": "#4a6e50",

    # UI Buttons
    "@btn-primary": "#3b6345",
    "@btn-primary-hover": "#467552",
    "@btn-primary-border": "#4d7a58",
    "@btn-secondary": "#1b232e",
    "@btn-secondary-hover": "#253040",
    "@btn-secondary-border": "#2a3647",
    
    # Plot colors (dark mode)
    "@plot-bg-dark": "none",
    "@plot-text-dark": "#f0f3f6",
    "@plot-line-dark": "#b0b8c4",
    "@plot-grid-dark": "#333333",
    "@plot-point-dark": "#ffe135",
    "@plot-edge-dark": "#1e1e1e",
    "@plot-accent-dark": "#90c527",
    
    # Plot colors (light mode)
    "@plot-bg-light": "white",
    "@plot-text-light": "black",
    "@plot-line-light": "black",
    "@plot-grid-light": "#dddddd",
    "@plot-point-light": "#ffe135",
    "@plot-edge-light": "black",
    "@plot-accent-light": "#40a02b",
    
    # Special Plot Backgrounds
    "@plot-feldspar-bg-dark": "#161b22",
    "@plot-feldspar-bg-light": "white",
    
    # Python-specific animations for buttons
    "@anim-btn-primary-base-bg": "#2e4a35",
    "@anim-btn-primary-base-border": "#3b6345",
    "@anim-btn-primary-hover-bg": "#467552",
    "@anim-btn-primary-hover-border": "#558762",
    
    "@anim-btn-secondary-base-bg": "#1b232e",
    "@anim-btn-secondary-base-border": "#2a3647",
    "@anim-btn-secondary-hover-bg": "#253040",
    "@anim-btn-secondary-hover-border": "#354459",
    
    "@anim-toggle-base-bg": "#222831",
    "@anim-toggle-hover-bg": "#2a313b",
    "@anim-toggle-base-text": "#7a818c",
    "@anim-toggle-hover-text": "#d1d7e0",
    "@anim-toggle-checked-bg": "#1a3024",
    "@anim-toggle-checked-border": "#90c527",
    "@anim-toggle-checked-text": "#90c527",
}

# Dict for python without @ symbol
colors = {k.replace('@', ''): v for k, v in COLORS.items()}

def hex_to_rgb(hex_str):
    """Converts a hex string like '#RRGGBB' to an (R, G, B) tuple of ints."""
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        # Fallback for named colors like 'none', 'black', 'orange' (will return 0,0,0 just in case)
        return (0, 0, 0)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
