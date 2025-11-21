import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, default_n_shown_samples=600):
    logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    # ==========================================
    # 🔧 MANEJO ROBUSTO DE ZOOM + SLIDER
    # ==========================================
    x_min, x_max = None, None

    if relayout_data:

        # Caso 1 — Zoom con ratón: xaxis.range[0] y [1]
        if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range[0]"])
            x_max = pd.to_datetime(relayout_data["xaxis.range[1]"])
            logging.info(f"Zoom ratón detectado: {x_min} → {x_max}")

        # Caso 2 — Slider: xaxis.range = [min, max]
        elif "xaxis.range" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range"][0])
            x_max = pd.to_datetime(relayout_data["xaxis.range"][1])
            logging.info(f"Slider detectado: {x_min} → {x_max}")

        # Caso 3 — Auto-reseteo (doble click)
        elif "xaxis.autorange" in relayout_data:
            x_min, x_max = None, None
            logging.info("Autoreset detectado (doble click)")

    # ==========================================
    # 📌 Filtrado del dataframe visible
    # ==========================================
    if x_min is None or x_max is None:
        df_visible = df_plot
    else:
        df_visible = df_plot[(df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)]

    # ==========================================
    # 📈 Figura con resampler
    # ==========================================
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    y_min_global, y_max_global = None, None

    # ==========================================
    # 📌 Añadir series principales
    # ==========================================
    for col in columnas_seleccionadas:
        etiqueta = format_label_with_unit(col)
        serie = df_visible[[x_timer, col]].copy()

        # Filtrar valores válidos
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

    # ==========================================
    # 📌 Marcadores de anomalías
    # ==========================================
    marker_base_y = y_min_global if y_min_global is not None else 0

    for col in columnas_seleccionadas:
        # -999999 (anómalos)
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

        # 999999 (nulos)
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

    # ==========================================
    # 📌 Slider
    # ==========================================
    slider_min, slider_max = df_plot[x_timer].min(), df_plot[x_timer].max()

    # ==========================================
    # 🎨 Aplicar layout modular
    # ==========================================
    fig.update_layout(get_graph_layout(x_min, x_max, slider_min, slider_max))

    return fig
