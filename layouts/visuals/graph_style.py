from .slider_style import get_slider_style
from .legend_style import get_legend_style
from .axes_style import get_axes_style

from .styles.graphs import graph_styles_dict

def get_graph_layout(x_min=None, x_max=None, slider_min=None, slider_max=None):
    """
    Combina los subcomponentes visuales del gráfico principal.
    """
    slider_style = get_slider_style(slider_min, slider_max)
    axes_style = get_axes_style(x_min, x_max, slider_style)
    legend_style = get_legend_style()


    # graph_styles_name ="classic"
    # graph_styles_name ="dark"
    # graph_styles_name ="professional"
    # graph_styles_name ="terminal"
    # graph_styles_name ="minimal"
    # graph_styles_name ="alert"  
    # graph_styles_name ="scientific"
    # graph_styles_name ="compact"

    graph_styles_name ="glass1"

    base_style = dict(graph_styles_dict.get(graph_styles_name, {}))

    # fig_layout = dict(
    #     # title="Evolución temporal (resampleado dinámico)",
    #     xaxis_title="Fecha y Hora",
    #     yaxis_title="Valor",
    #     hovermode='x unified',
    #     plot_bgcolor="#D7E1CC",
    #     paper_bgcolor="#FFFFFF",
    #     font=dict(
    #         color='#000000',  # Negro
    #         family='Arial, sans-serif',
    #         size=15,
    #         weight='bold'  # Negrita
    #     ),
    #     **axes_style,
    #     legend=legend_style
    # )

    fig_layout = dict(
        xaxis_title="Fecha y Hora",
        yaxis_title="Valor",
        **base_style,
        **axes_style,
        legend=legend_style
    )

    return fig_layout
