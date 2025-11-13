import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, default_n_shown_samples=400):
    logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    # --- Asegurar formato correcto ---
    df_plot = df_plot.copy()
    df_plot[x_timer] = pd.to_datetime(df_plot[x_timer], errors='coerce')

    x_min, x_max = None, None
    if relayout_data:
        if 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
            x_min = pd.to_datetime(relayout_data['xaxis.range[0]'])
            x_max = pd.to_datetime(relayout_data['xaxis.range[1]'])
            logging.info(f"Nuevo rango detectado: {x_min} → {x_max}")

    df_visible = df_plot if x_min is None else df_plot[(df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)]
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    # --- Determinar resolución temporal ---
    try:
        res_td = df_plot[x_timer].sort_values().diff().mode()[0]
        resolution_seconds = res_td.total_seconds()
    except Exception:
        resolution_seconds = 10.0  # fallback si no se puede calcular

    margen = 0.5
    threshold = resolution_seconds + margen

    # --- Graficar columnas ---
    y_min_global, y_max_global = None, None
    for col in columnas_seleccionadas:
        etiqueta = format_label_with_unit(col)
        serie = df_visible[[x_timer, col]].copy()
        serie[col] = pd.to_numeric(serie[col], errors='coerce')  # asegurar que es numérico

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

    marker_base_y = y_min_global if y_min_global is not None else 0

    # --- Dibujar puntos anómalos y nulos ---
    for col, color, val in [(col, "orange", -999999.0) for col in columnas_seleccionadas] + \
                           [(col, "red", 999999.0) for col in columnas_seleccionadas]:
        serie_err = df_visible[df_visible[col] == val]
        if not serie_err.empty:
            fig.add_trace(
                go.Scatter(
                    x=serie_err[x_timer],
                    y=[marker_base_y] * len(serie_err),
                    mode='markers',
                    marker=dict(color=color, size=10, symbol='square'),
                    showlegend=False
                )
            )

    # --- Función para detectar secuencias consecutivas ---
    def detectar_secuencias(df_col, valor, color):
        regiones = []
        serie = df_visible[df_visible[df_col] == valor].sort_values(x_timer)
        if serie.empty:
            return regiones

        ts = pd.to_datetime(serie[x_timer]).reset_index(drop=True)
        if len(ts) == 1:
            start = ts.iloc[0] - pd.to_timedelta(resolution_seconds / 2, unit='s')
            end = ts.iloc[0] + pd.to_timedelta(resolution_seconds / 2, unit='s')
            regiones.append((start, end, color))
            return regiones

        diffs = ts.diff().dt.total_seconds().fillna(threshold + 1)
        group_id = (diffs > threshold).cumsum()
        for _, grp in pd.DataFrame({'ts': ts, 'gid': group_id}).groupby('gid'):
            start = grp['ts'].iloc[0] - pd.to_timedelta(resolution_seconds / 2, unit='s')
            end = grp['ts'].iloc[-1] + pd.to_timedelta(resolution_seconds / 2, unit='s')
            regiones.append((start, end, color))
        return regiones

    # --- Calcular zonas rojas y naranjas ---
    shaded_regions = []
    for col in columnas_seleccionadas:
        shaded_regions += detectar_secuencias(col, 999999.0, "red")
        shaded_regions += detectar_secuencias(col, -999999.0, "orange")

    # --- Añadir sombreado ---
    for (start, end, color) in shaded_regions:
        fig.add_vrect(
            x0=start,
            x1=end,
            fillcolor=color,
            opacity=0.2,
            layer="below",
            line_width=0
        )

    slider_min, slider_max = df_plot[x_timer].min(), df_plot[x_timer].max()
    fig.update_layout(get_graph_layout(x_min, x_max, slider_min, slider_max))
    return fig
