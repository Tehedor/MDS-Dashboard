import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout

def actualizar_grafico(columnas_seleccionadas, relayout_data, df_plot, x_timer, format_label_with_unit, default_n_shown_samples=600):
    logging.info(f"Callback ejecutado con columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Por favor, selecciona al menos una serie.")

    df_plot = df_plot.copy()
    df_plot[x_timer] = pd.to_datetime(df_plot[x_timer], errors='coerce')

    x_min, x_max = None, None
    if relayout_data and 'xaxis.range[0]' in relayout_data and 'xaxis.range[1]' in relayout_data:
        x_min = pd.to_datetime(relayout_data['xaxis.range[0]'])
        x_max = pd.to_datetime(relayout_data['xaxis.range[1]'])
        logging.info(f"Nuevo rango detectado: {x_min} → {x_max}")

    df_visible = df_plot if x_min is None else df_plot[(df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)]
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    # --- Calcular resolución temporal ---
    try:
        res_td = df_plot[x_timer].sort_values().diff().mode()[0]
        resolution_seconds = res_td.total_seconds()
    except Exception:
        resolution_seconds = 10.0
    margen = 0.5
    threshold = resolution_seconds + margen

    y_min_global, y_max_global = None, None

    # --- Graficar series válidas ---
    for col in columnas_seleccionadas:
        etiqueta = format_label_with_unit(col)
        serie = df_visible[[x_timer, col]].copy()
        serie[col] = pd.to_numeric(serie[col], errors='coerce')

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
    def detectar_secuencias(df_col, valor):
        serie = df_visible[df_visible[df_col] == valor].sort_values(x_timer)
        if serie.empty:
            return []

        ts = pd.to_datetime(serie[x_timer]).reset_index(drop=True)
        diffs = ts.diff().dt.total_seconds().fillna(threshold + 1)
        group_id = (diffs > threshold).cumsum()
        regiones = []
        for _, grp in pd.DataFrame({'ts': ts, 'gid': group_id}).groupby('gid'):
            start = grp['ts'].iloc[0] - pd.to_timedelta(resolution_seconds / 2, unit='s')
            end = grp['ts'].iloc[-1] + pd.to_timedelta(resolution_seconds / 2, unit='s')
            color = "red" if valor == 999999.0 else "orange"
            regiones.append((start, end, color))
        return regiones

    # --- Calcular zonas a sombrear ---
    shaded_regions = []
    for col in columnas_seleccionadas:
        shaded_regions += detectar_secuencias(col, 999999.0)
        shaded_regions += detectar_secuencias(col, -999999.0)

    # --- Fusionar intervalos superpuestos ---
    def fusionar_intervalos(intervalos):
        if not intervalos:
            return []
        intervalos.sort(key=lambda x: x[0])
        merged = [intervalos[0]]
        for current in intervalos[1:]:
            last = merged[-1]
            if current[0] <= last[1] and current[2] == last[2]:  # mismo color
                merged[-1] = (last[0], max(last[1], current[1]), last[2])
            else:
                merged.append(current)
        return merged

    shaded_regions = fusionar_intervalos(shaded_regions)

    # --- Añadir sombreado usando Scatter relleno (mucho más rápido) ---
    for start, end, color in shaded_regions:
        fig.add_trace(go.Scatter(
            x=[start, end, end, start],
            y=[y_min_global, y_min_global, y_max_global, y_max_global],
            fill='toself',
            fillcolor=color,
            line=dict(width=0),
            opacity=0.2,
            hoverinfo='skip',
            showlegend=False
        ))

    slider_min, slider_max = df_plot[x_timer].min(), df_plot[x_timer].max()
    fig.update_layout(get_graph_layout(x_min, x_max, slider_min, slider_max))

    return fig
