# callbacks/grafico_temporal.py

import logging
import gc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pcolors
from plotly_resampler import FigureResampler
from plotly_resampler.aggregation import EveryNthPoint
from layouts.visuals.graph_style import get_graph_layout

log = logging.getLogger("grafico_temporal")

def complementary_color(color):
    if color.startswith("#"):
        color = color.lstrip("#")
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    else:
        r, g, b = map(int, color.strip("rgb()").split(","))
    return f"rgb({255-r},{255-g},{255-b})"

def actualizar_grafico(
    columnas_seleccionadas, relayout_data, df_plot, x_timer,
    format_label_with_unit, columnas_info, slider_data,
    event_dictionary=None, default_n_shown_samples=1000,
):
    gc.collect()
    event_dictionary = event_dictionary or {}
    if not columnas_seleccionadas: return go.Figure()

    # 1. TIEMPOS Y TU
    full_x = df_plot[x_timer].values.astype("datetime64[ns]")
    # ... (lógica de tu_ns se mantiene igual) ...
    if len(full_x) > 1:
        tu_ns = np.median(np.diff(full_x[:50].view(np.int64)))
        if tu_ns <= 0: tu_ns = 60 * 1e9
    else: tu_ns = 60 * 1e9
    tu_tolerance_ns = tu_ns * 1.5

    # 2. RANGOS Y VISTA (CORREGIDO)
    slider_min = pd.to_datetime(slider_data["min"]) if slider_data else pd.to_datetime(full_x[0])
    slider_max = pd.to_datetime(slider_data["max"]) if slider_data else pd.to_datetime(full_x[-1])

    x_min, x_max = None, None

    # Lógica robusta para leer relayout_data
    if relayout_data:
        if "xaxis.range[0]" in relayout_data:
            # Caso: Zoom directo en el gráfico
            x_min = relayout_data["xaxis.range[0]"]
            x_max = relayout_data["xaxis.range[1]"]
        elif "xaxis.range" in relayout_data:
            # Caso: Movimiento desde el Slider
            x_min = relayout_data["xaxis.range"][0]
            x_max = relayout_data["xaxis.range"][1]
        elif "xaxis.autorange" in relayout_data:
            # Caso: Doble click para resetear
            x_min, x_max = None, None

    if x_min is None:
        idx_start, idx_end = 0, len(full_x)
        view_min, view_max = slider_min, slider_max
    else:
        view_min, view_max = pd.to_datetime(x_min), pd.to_datetime(x_max)
        # Aseguramos que view_min/max estén dentro de los límites absolutos para evitar errores de índice
        if view_min < slider_min: view_min = slider_min
        if view_max > slider_max: view_max = slider_max
        
        idx_start = np.searchsorted(full_x, view_min.to_datetime64())
        idx_end = np.searchsorted(full_x, view_max.to_datetime64())

    x_view = full_x[idx_start:idx_end]

    # 3. GAPS (Detección e índices para NaNs)
    gap_timestamps, gap_indices = [], []
    if len(x_view) > 1:
        x_diff = np.diff(x_view.view(np.int64))
        gap_mask = x_diff > tu_tolerance_ns
        gap_timestamps = x_view[:-1][gap_mask]
        gap_indices = np.where(gap_mask)[0] + 1

    # 4. FIGURA
    fig = FigureResampler(go.Figure(), default_downsampler=EveryNthPoint(), default_n_shown_samples=default_n_shown_samples)
    palette = pcolors.qualitative.Plotly

    # 4.1 GHOST TRACES (Recortados)
    step = max(1, len(full_x) // 2000)
    x_bg = full_x[::step]
    mask_in_view = (x_bg >= view_min.to_datetime64()) & (x_bg <= view_max.to_datetime64())

    for col in columnas_seleccionadas:
        if col.endswith("-from_to"): continue
        col_name = col.split("::")[-1]
        if col_name in df_plot.columns:
            y_bg = pd.to_numeric(df_plot[col_name].values[::step], errors="coerce").astype(float)
            y_bg[mask_in_view] = np.nan # Eliminar sombra donde hay datos reales
            color = palette[sum(ord(c) for c in col_name) % len(palette)]
            fig.add_trace(go.Scattergl(x=x_bg, y=y_bg, mode="lines", line=dict(width=1, color=color), opacity=0.2, showlegend=False, hoverinfo="skip", connectgaps=False))

    # 5. SERIES PRINCIPALES
    all_numeric_values, fromto_points = [], {}
    selected_vars = [c.split("::")[-1] for c in columnas_seleccionadas]

    for col in columnas_seleccionadas:
        col_name = col.split("::")[-1]
        if col_name not in df_plot.columns: continue
        y_raw = df_plot[col_name].values[idx_start:idx_end]

        # --- MODIFICACIÓN AQUÍ ---
        if col_name.endswith("-from_to"):
            base_v = col_name.replace("-from_to", "")
            if base_v in selected_vars:
                y_base = pd.to_numeric(df_plot[base_v].values[idx_start:idx_end], errors="coerce")
                y_codes = pd.to_numeric(y_raw, errors="coerce")
                
                for i, v in enumerate(y_codes):
                    if not pd.isna(v) and v not in (-999999, 999999):
                        full_label = event_dictionary.get(int(v), f"Ev:{int(v)}")
                        
                        # Limpieza: Si la etiqueta empieza con el nombre de la variable, lo quitamos
                        if full_label.startswith(base_v):
                            # Quitamos el nombre base y el posible guion bajo inicial
                            clean_label = full_label[len(base_v):].lstrip("_")
                        else:
                            clean_label = full_label

                        fromto_points.setdefault(base_v, []).append((x_view[i], y_base[i], clean_label, int(v)))
            continue
        # -------------------------

        y = pd.to_numeric(y_raw, errors="coerce")
        if np.any(~np.isnan(y)):
            all_numeric_values.append(y[~np.isnan(y)])
            color = palette[sum(ord(c) for c in col_name) % len(palette)]
            # Inserción de NaNs para romper líneas en Gaps
            y_vis = np.insert(y, gap_indices, np.nan) if len(gap_indices) > 0 else y
            x_vis = np.insert(x_view, gap_indices, x_view[gap_indices-1]) if len(gap_indices) > 0 else x_view
            
            short_label = format_label_with_unit(columnas_info, col).split("::")[-1]
            fig.add_trace(go.Scattergl(name=short_label, line=dict(width=2, color=color), connectgaps=False), hf_x=x_vis, hf_y=y_vis)

    # 6. GAPS (Puntos X)
    if all_numeric_values and len(gap_timestamps) > 0:
        mean_y = np.mean(np.concatenate(all_numeric_values))
        fig.add_trace(go.Scattergl(mode="markers", marker=dict(color="red", size=8, symbol="x-thin", line=dict(width=2)), name="Gap", hoverinfo="x"), hf_x=gap_timestamps, hf_y=np.full(len(gap_timestamps), mean_y))

    # 7. EVENTOS
    for base_v, pts in fromto_points.items():
        color = palette[sum(ord(c) for c in base_v) % len(palette)]
        fig.add_trace(go.Scattergl(mode="markers", marker=dict(color=complementary_color(color), size=10, line=dict(width=1, color=color)), name=f"Eventos:{base_v}", 
            customdata=[[p[2], p[3]] for p in pts], hovertemplate="<b>Estado:</b> %{customdata[0]}<br><b>Cod:</b> %{customdata[1]}<extra></extra>"), hf_x=[p[0] for p in pts], hf_y=[p[1] for p in pts])

    # 8. LAYOUT
    fig.update_layout(get_graph_layout(view_min, view_max, slider_min, slider_max), uirevision=f"{slider_min}_{slider_max}")
    fig.update_xaxes(range=[view_min, view_max], autorange=False, rangeslider=dict(visible=True, range=[slider_min, slider_max]))
    fig.update_yaxes(autorange=True, zeroline=False)
    
    gc.collect()
    return fig