# callbacks/grafico_temporal.py

import logging
import gc
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pcolors
from plotly_resampler import FigureResampler
from plotly_resampler.aggregation import EveryNthPoint
from layouts.visuals.graph_style import get_graph_layout

log = logging.getLogger("grafico_temporal")

# =====================================================================
# 🔄 ACTUALIZAR GRÁFICO — Slider Contextual (Sin Sombra)
# =====================================================================
def actualizar_grafico(
    columnas_seleccionadas,
    relayout_data,
    df_plot,
    x_timer,
    format_label_with_unit,
    columnas_info,
    slider_data,
    event_dictionary=None,
    default_n_shown_samples=1000,
):

    gc.collect()

    if event_dictionary is None:
        event_dictionary = {}

    if not columnas_seleccionadas:
        return go.Figure()

    # -------------------------------------------------
    # 1. PREPARACIÓN DE TIEMPOS Y TU
    # -------------------------------------------------
    full_x = df_plot[x_timer].values.astype("datetime64[ns]")

    # Detección robusta de Tu
    if len(full_x) > 1:
        chunk = full_x[:50].view(np.int64)
        diffs = np.diff(chunk)
        tu_ns = np.median(diffs)
        if tu_ns <= 0: tu_ns = 60 * 1e9
    else:
        tu_ns = 60 * 1e9
    
    tu_tolerance_ns = tu_ns * 1.5

    # -------------------------------------------------
    # 2. RANGOS GLOBALES Y DE VISTA
    # -------------------------------------------------
    if slider_data:
        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])
    else:
        slider_min = pd.to_datetime(full_x[0])
        slider_max = pd.to_datetime(full_x[-1])

    x_min, x_max = None, None
    if relayout_data:
        if "xaxis.range[0]" in relayout_data:
            x_min = relayout_data["xaxis.range[0]"]
            x_max = relayout_data["xaxis.range[1]"]
        elif "xaxis.range" in relayout_data:
            try:
                x_min, x_max = relayout_data["xaxis.range"]
            except Exception:
                pass
        
        if relayout_data.get("xaxis.autorange") is True:
            x_min = x_max = None

    if x_min is None or x_max is None:
        idx_start = 0
        idx_end = len(full_x)
        view_min, view_max = slider_min, slider_max
    else:
        tmin = pd.to_datetime(x_min).to_datetime64()
        tmax = pd.to_datetime(x_max).to_datetime64()
        idx_start = np.searchsorted(full_x, tmin)
        idx_end = np.searchsorted(full_x, tmax)
        view_min, view_max = x_min, x_max

    x_view = full_x[idx_start:idx_end]

    # -------------------------------------------------
    # 3. DETECCIÓN DE HUECOS (GAPS)
    # -------------------------------------------------
    gap_timestamps = []
    gap_indices = []
    
    if len(x_view) > 1:
        x_view_int = x_view.view(np.int64)
        x_diff = np.diff(x_view_int)
        
        gap_mask = x_diff > tu_tolerance_ns
        gap_timestamps = x_view[:-1][gap_mask]
        gap_indices = np.where(gap_mask)[0] + 1

    # -------------------------------------------------
    # 4. INICIALIZAR FIGURA
    # -------------------------------------------------
    gc.collect()
    fig = FigureResampler(
        go.Figure(),
        default_downsampler=EveryNthPoint(),
        default_n_shown_samples=default_n_shown_samples,
    )
    
    palette = pcolors.qualitative.Plotly
    
    # -------------------------------------------------
    # 4.1 TRAZAS DE CONTEXTO GLOBAL (Recortadas en la vista)
    # -------------------------------------------------
    total_points = len(full_x)
    step = max(1, total_points // 2000)
    x_bg = full_x[::step]

    # Convertimos los límites de la vista actual a datetime64 para comparar
    v_min_dt = pd.to_datetime(view_min).to_datetime64()
    v_max_dt = pd.to_datetime(view_max).to_datetime64()

    # Creamos una máscara: True si el punto está DENTRO de lo que estamos viendo ahora
    mask_in_view = (x_bg >= v_min_dt) & (x_bg <= v_max_dt)

    for col in columnas_seleccionadas:
        if col.endswith("-from_to"):
            continue
            
        col_name = col.split("::")[-1]
        if col_name in df_plot.columns:
            # Obtenemos datos downsampled
            y_bg = df_plot[col_name].values[::step]
            y_bg = pd.to_numeric(y_bg, errors='coerce').astype(float)
            
            # TRUCO: Ponemos a NaN los puntos que están en la pantalla actual.
            # Así desaparece la "sombra" detrás de los datos reales, 
            # pero se mantiene en el resto del slider.
            y_bg[mask_in_view] = np.nan
            
            char_sum = sum(ord(c) for c in col_name)
            fixed_color = palette[char_sum % len(palette)]

            fig.add_trace(
                go.Scattergl(
                    x=x_bg, 
                    y=y_bg,
                    mode='lines',
                    line=dict(width=1, color=fixed_color), 
                    opacity=0.3, 
                    showlegend=False,
                    hoverinfo='skip',
                    connectgaps=False, # Importante: no unir los cortes que acabamos de hacer
                    name="Contexto"
                )
            )

    # -------------------------------------------------
    # 5. COLUMNAS PRINCIPALES (ALTA RESOLUCIÓN)
    # -------------------------------------------------
    all_numeric_values = []
    fromto_points = []
    has_numeric_data = False
    
    for col in columnas_seleccionadas:
        col_name = col.split("::")[-1]
        if col_name not in df_plot.columns:
            continue

        y_raw = df_plot[col_name].values[idx_start:idx_end]

        # --- EVENTOS ---
        if col_name.endswith("-from_to"):
            base_clean = col_name.replace("-from_to", "")
            base_clean = "_".join(
                [p for p in base_clean.split("_") if not p.startswith("Q")]
            )
            y_base = pd.to_numeric(df_plot[base_clean].values[idx_start:idx_end], errors="coerce") if base_clean in df_plot.columns else np.zeros_like(y_raw)
            y_codes = pd.to_numeric(y_raw, errors="coerce")
            for i, v in enumerate(y_codes):
                if pd.isna(v) or v in (-999999, 999999): continue
                event_name = event_dictionary.get(int(v), "Evento desconocido") if not pd.isna(v) else "N/A"
                fromto_points.append((x_view[i], y_base[i], event_name, v))
            continue

        # --- SERIES NUMÉRICAS ---
        y = pd.to_numeric(y_raw, errors="coerce")
        valid_mask = ~np.isnan(y)

        if np.any(valid_mask):
            yy = y[valid_mask]
            all_numeric_values.append(yy)
            has_numeric_data = True

            # Color Fijo
            char_sum = sum(ord(c) for c in col_name)
            fixed_color = palette[char_sum % len(palette)]
            
            # 🛠 FIX GAPS VISUALES (Líneas fantasmas en huecos)
            if len(gap_indices) > 0:
                y_visual = np.insert(y, gap_indices, np.nan)
                x_visual = np.insert(x_view, gap_indices, x_view[gap_indices-1])
            else:
                y_visual = y
                x_visual = x_view

            # Etiqueta corta
            full_label = format_label_with_unit(columnas_info, col)
            short_label = full_label.split("::")[-1]

            fig.add_trace(
                go.Scattergl(
                    name=short_label,
                    line=dict(width=2, color=fixed_color),
                    connectgaps=False, 
                ),
                hf_x=x_visual,
                hf_y=y_visual,
            )

    # -------------------------------------------------
    # 6. GAPS Y MEDIA GLOBAL
    # -------------------------------------------------
    global_mean_y = 0
    if has_numeric_data:
        combined_data = np.concatenate(all_numeric_values)
        global_mean_y = np.mean(combined_data)

    if has_numeric_data and len(gap_timestamps) > 0:
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="red", size=8, symbol="x-thin", line=dict(width=2)),
                name="Gap detectado",
                hoverinfo="x",
            ),
            hf_x=gap_timestamps,
            hf_y=np.full(len(gap_timestamps), global_mean_y),
        )

    # -------------------------------------------------
    # 7. EVENTOS
    # -------------------------------------------------
    if fromto_points:
        xs = [p[0] for p in fromto_points]
        ys = [p[1] for p in fromto_points]
        cdata = [[p[2], p[3]] for p in fromto_points]

        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="blue", size=7),
                name="Eventos",
                customdata=cdata,
                hovertemplate=("<b>Evento:</b> %{customdata[0]}<br><b>Código:</b> %{customdata[1]}<extra></extra>"),
            ),
            hf_x=xs, hf_y=ys,
        )

    # -------------------------------------------------
    # 8. LAYOUT + UIREVISION
    # -------------------------------------------------
    user_interaction_uid = f"{slider_min}_{slider_max}"

    fig.update_layout(
        get_graph_layout(view_min, view_max, slider_min, slider_max)
    )

    fig.update_layout(
        uirevision=user_interaction_uid
    )

    fig.update_xaxes(
        range=[view_min, view_max],
        autorange=False,
        rangeslider=dict(
            visible=True,
            range=[slider_min, slider_max],
        ),
    )

    fig.update_yaxes(
        autorange=True, 
        zeroline=False
    )

    gc.collect()
    return fig