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
    
    # Translate TAS labels according to active language
    from utils.i18n import tr
    tas_trans_map = {
        'Alkalic\nBasalt': 'tas_alkalic_basalt',
        'Subalkalic\nBasalt': 'tas_subalkalic_basalt',
        'Foidite': 'tas_foidite',
        'Basaltic\nAndesite': 'tas_basaltic_andesite',
        'Andesite': 'tas_andesite',
        'Dacite': 'tas_dacite',
        'Picrite': 'tas_picrite',
        'Phonolite': 'tas_phonolite',
        'Rhyolite': 'tas_rhyolite',
        'Trachy-\nbasalt': 'tas_trachy_basalt',
        'Basaltic\nTrachy-\nandesite': 'tas_basaltic_trachy_andesite',
        'Trachy-\nandesite': 'tas_trachy_andesite',
        'Trachyte': 'tas_trachyte',
        'Trachydacite': 'tas_trachydacite',
        'Tephrite': 'tas_tephrite',
        'Phonotephrite': 'tas_phonotephrite',
        'Tephriphonolite': 'tas_tephriphonolite',
        'Alkalic\nGabbro': 'tas_alkalic_gabbro',
        'Subalkalic\nGabbro': 'tas_subalkalic_gabbro',
        'Foidolite': 'tas_foidolite',
        'Gabbroic\nDiorite': 'tas_gabbroic_diorite',
        'Diorite': 'tas_diorite',
        'Granodiorite': 'tas_granodiorite',
        'Peridot-\ngabbro': 'tas_peridot_gabbro',
        'Foid\nSyenite': 'tas_foid_syenite',
        'Granite': 'tas_granite',
        'Monzo-\ngabbro': 'tas_monzo_gabbro',
        'Monzo-\ndiorite': 'tas_monzo_diorite',
        'Monzonite': 'tas_monzonite',
        'Syenite': 'tas_syenite',
        'Quartz\nMonzonite': 'tas_quartz_monzonite',
        'Foid\nGabbro': 'tas_foid_gabbro',
        'Foid\nMonzodiorite': 'tas_foid_monzodiorite',
        'Foid\nMonzosyenite': 'tas_foid_monzosyenite',
    }

    # Update label text colors and localized strings
    for t in ax.texts:
        raw_text = t.get_text()
        if raw_text in tas_trans_map:
            t.set_text(tr(tas_trans_map[raw_text]))
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
