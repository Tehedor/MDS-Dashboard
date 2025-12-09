# callbacks/grafico_temporal.py
import logging
import gc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from plotly_resampler.aggregation import EveryNthPoint
from layouts.visuals.graph_style import get_graph_layout


def actualizar_grafico(
    columnas_seleccionadas,
    relayout_data,
    df_plot,
    x_timer,
    format_label_with_unit,
    columnas_info,
    slider_data,
    default_n_shown_samples=550,
):
    """
    Gráfico temporal con:
      - Slider fijo
      - Manejo correcto del zoom y desplazamiento
      - Marcadores únicos para anómalos/nulos
      - Puntos from_to situados a la altura de la columna base
    """

    gc.collect()

    # ---------------------------------------------------------------------
    # 0. Sin columnas seleccionadas
    # ---------------------------------------------------------------------
    if not columnas_seleccionadas:
        return go.Figure().update_layout(
            title="Por favor, selecciona al menos una serie."
        )

    # ---------------------------------------------------------------------
    # 1. Rango absoluto del slider
    # ---------------------------------------------------------------------
    if slider_data is not None:
        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])
    else:
        tmp_x = pd.to_datetime(df_plot[x_timer])
        slider_min = tmp_x.iloc[0]
        slider_max = tmp_x.iloc[-1]

    full_x_values = df_plot[x_timer].values

    # ---------------------------------------------------------------------
    # 2. Procesar zoom / movimiento del slider
    # ---------------------------------------------------------------------
    x_min, x_max = None, None

    if relayout_data:

        # Caso 1: Zoom sobre la gráfica
        if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
            x_min = relayout_data["xaxis.range[0]"]
            x_max = relayout_data["xaxis.range[1]"]

        # Caso 2: Desplazar ventana del slider
        elif "xaxis.range" in relayout_data:
            try:
                x_min, x_max = relayout_data["xaxis.range"]
            except Exception:
                x_min = x_max = None

        # Reset (doble clic)
        if relayout_data.get("xaxis.autorange") is True:
            x_min = x_max = None

    # ---------------------------------------------------------------------
    # 3. Slicing según ventana visible
    # ---------------------------------------------------------------------
    if x_min is None or x_max is None:
        # Vista general
        idx_start, idx_end = 0, len(full_x_values)
        current_view_min, current_view_max = slider_min, slider_max
    else:
        tmin = pd.to_datetime(x_min).to_datetime64()
        tmax = pd.to_datetime(x_max).to_datetime64()

        idx_start = np.searchsorted(full_x_values, tmin)
        idx_end = np.searchsorted(full_x_values, tmax)

        idx_start = max(0, idx_start)
        idx_end = min(len(full_x_values), idx_end)

        current_view_min, current_view_max = x_min, x_max

    if idx_end <= idx_start:
        idx_start, idx_end = 0, len(full_x_values)
        current_view_min, current_view_max = slider_min, slider_max

    x_view = full_x_values[idx_start:idx_end]

    # ---------------------------------------------------------------------
    # 4. Crear figura resampleada
    # ---------------------------------------------------------------------
    fig = FigureResampler(
        go.Figure(),
        default_downsampler=EveryNthPoint(),
        default_n_shown_samples=default_n_shown_samples,
    )

    y_min_global, y_max_global = None, None

    # ---------------------------------------------------------------------
    # 5. Detección de anomalías / nulos / from_to
    # ---------------------------------------------------------------------
    anomalous_timestamps = []     # -999999 → Naranja
    null_timestamps = []          #  999999 → Rojo
    fromto_points = []            # (x, y_base, valor_fromto, col_name)

    for col in columnas_seleccionadas:

        col_name = col.split("::")[-1]

        if col_name not in df_plot.columns:
            continue

        y_full = df_plot[col_name].values
        y_view = y_full[idx_start:idx_end]

        if len(y_view) == 0:
            continue

        # ------------------------------------------------------------
        # 5A. FROM_TO → puntos en altura del valor base
        # ------------------------------------------------------------
        if col_name.endswith("-from_to"):
            col_base = col_name.replace("-from_to", "")

            if col_base in df_plot.columns:
                base_vals = df_plot[col_base].values[idx_start:idx_end]

                for i, v_fromto in enumerate(y_view):
                    if not np.isnan(v_fromto) and v_fromto not in (-999999, 999999):
                        fromto_points.append(
                            (x_view[i], base_vals[i], v_fromto, col_name)
                        )

            continue  # no se pinta línea

        # ------------------------------------------------------------
        # 5B. Valores anómalos / nulos
        # ------------------------------------------------------------
        is_anomaly = y_view == -999999.0
        is_null = y_view == 999999.0
        is_invalid = is_anomaly | is_null

        if np.any(is_anomaly):
            anomalous_timestamps.extend(x_view[is_anomaly])

        if np.any(is_null):
            null_timestamps.extend(x_view[is_null])

        # ------------------------------------------------------------
        # 5C. Valores válidos → pintar línea normal
        # ------------------------------------------------------------
        is_valid = ~(is_invalid) & (y_view > -999998.0) & (y_view < 999998.0)

        if np.any(is_valid):
            valid_y = y_view[is_valid]
            ymin, ymax = np.min(valid_y), np.max(valid_y)

            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scattergl(
                    name=format_label_with_unit(col),
                    line=dict(width=3),
                ),
                hf_x=x_view[is_valid],
                hf_y=valid_y,
            )

        del y_view, is_valid, is_invalid, is_anomaly, is_null

    # ---------------------------------------------------------------------
    # 5D. Dibujar anomalías / nulos
    # ---------------------------------------------------------------------
    base_y = 0 if y_min_global is None else y_min_global - abs(y_min_global) * 0.05

    # ANÓMALOS
    if len(anomalous_timestamps) > 0:
        ts = np.unique(anomalous_timestamps)
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="orange", size=8, symbol="square"),
                name="Anómalos (-999999)",
            ),
            hf_x=ts,
            hf_y=np.full(len(ts), base_y),
        )

    # NULOS
    if len(null_timestamps) > 0:
        ts = np.unique(null_timestamps)
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="red", size=8, symbol="square"),
                name="Nulos (999999)",
            ),
            hf_x=ts,
            hf_y=np.full(len(ts), base_y),
        )

    # ---------------------------------------------------------------------
    # 5E. Dibujar puntos FROM_TO en la altura real de la columna base
    # ---------------------------------------------------------------------
    if len(fromto_points) > 0:
        xs = [p[0] for p in fromto_points]
        ys = [p[1] for p in fromto_points]
        textos = [f"{p[3]}: {p[2]}" for p in fromto_points]

        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="blue", size=9, symbol="circle"),
                name="from_to",
                hovertemplate="%{text}<br>%{x}<extra></extra>",
                text=textos,
            ),
            hf_x=xs,
            hf_y=ys,
        )

    # ---------------------------------------------------------------------
    # 6. Layout
    # ---------------------------------------------------------------------
    layout_cfg = get_graph_layout(
        current_view_min,
        current_view_max,
        slider_min,
        slider_max,
    )
    fig.update_layout(layout_cfg)

    # ---------------------------------------------------------------------
    # 7. Slider fijo
    # ---------------------------------------------------------------------
    fig.update_xaxes(
        range=[current_view_min, current_view_max],
        autorange=False,
        rangeslider=dict(
            visible=True,
            range=[slider_min, slider_max],
        ),
    )

    return fig
