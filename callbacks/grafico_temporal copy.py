import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, default_n_shown_samples=400):
    logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    x_min, x_max = None, None
    if relayout_data:
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            x_min = pd.to_datetime(relayout_data['xaxis.range[0]'])
            x_max = pd.to_datetime(relayout_data['xaxis.range[1]'])
            logging.info(f"Nuevo rango detectado: {x_min} → {x_max}")

    df_visible = df_plot[(df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)] if x_min is not None else df_plot
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    # ...existing code...
    y_min_global, y_max_global = None, None
    for col in columnas_seleccionadas:
        etiqueta = format_label_with_unit(col)
        serie = df_visible[[x_timer, col]].copy()

        serie_validos = serie[serie[col].between(-999998.0, 999998.0)]
        if not serie_validos.empty:
            ymin, ymax = serie_validos[col].min(), serie_validos[col].max()
            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

        fig.add_trace(
            go.Scatter(name=etiqueta, line=dict(width=2)),
            hf_x=serie_validos[x_timer],
            hf_y=serie_validos[col]
        )

    # Determinar posición vertical para los marcadores de "huecos"
    marker_base_y = y_min_global if y_min_global is not None else 0

    # Añadir anomalías (-999999.0) colocadas en marker_base_y para que sean visibles
    for col in columnas_seleccionadas:
        serie_anomalos = df_visible[df_visible[col] == -999999.0]
        if not serie_anomalos.empty:
            fig.add_trace(
                go.Scatter(
                    x=serie_anomalos[x_timer],
                    y=[marker_base_y] * len(serie_anomalos),
                    mode='markers',
                    marker=dict(color='orange', size=10, symbol='square'),
                    showlegend=False
                )
            )
    
    # Añadir nulos (999999.0) colocados en marker_base_y para que sean visibles
    for col in columnas_seleccionadas:
        serie_nulos = df_visible[df_visible[col] == 999999.0]
        if not serie_nulos.empty:
            fig.add_trace(
                go.Scatter(
                    x=serie_nulos[x_timer],
                    y=[marker_base_y] * len(serie_nulos),
                    mode='markers',
                    marker=dict(color='red', size=10, symbol='square'),
                    showlegend=False
                )
            )

    slider_min, slider_max = df_plot[x_timer].min(), df_plot[x_timer].max()
    # ...existing code...

    # ✅ Aplicar layout modular
    fig.update_layout(get_graph_layout(x_min, x_max, slider_min, slider_max))
    return fig
