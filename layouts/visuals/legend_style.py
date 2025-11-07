# layouts/visuals/legend_style.py
from .styles.legends import legend_styles_dict

def get_legend_style():
    """Devuelve la configuración de la leyenda según el tema."""

    # legend_style_name = "classic"
    # legend_style_name = "light_top_right"
    # legend_style_name = "dark_overlay" # +
    # legend_style_name = "minimal" # +++
    # legend_style_name = "card_centered"
    # legend_style_name = "professional" # +++
    # legend_style_name = "left_vertical"
    # legend_style_name = "terminal"
    # legend_style_name = "alert"
    # legend_style_name = "compact"
    legend_style_name = "profesional_overtop"


    
    legend_style = dict(legend_styles_dict.get(legend_style_name, {}))

    # legend_style = dict(
    #     bgcolor='rgba(255,255,255,0.7)',
    #     bordercolor='rgba(0,0,0,0.3)',
    #     borderwidth=1,
    #     orientation="h",
    #     yanchor="bottom",
    #     y=-0.25,
    #     xanchor="center",
    #     x=0.5
    # )


    return legend_style