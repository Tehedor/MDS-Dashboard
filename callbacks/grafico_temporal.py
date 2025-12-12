# callbacks/grafico_temporal.py
import logging
import gc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from plotly_resampler.aggregation import EveryNthPoint
from layouts.visuals.graph_style import get_graph_layout

log = logging.getLogger("grafico_temporal")

# =====================================================================
# 🔄 ACTUALIZAR GRÁFICO — fully compatible with new blank mode
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

    # Slider range
    if slider_data:
        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])
    else:
        tmp = pd.to_datetime(df_plot[x_timer])
        slider_min, slider_max = tmp.iloc[0], tmp.iloc[-1]

    full_x = df_plot[x_timer].values

    # Zoom
    x_min, x_max = None, None
    if relayout_data:
        if "xaxis.range[0]" in relayout_data:
            x_min = relayout_data["xaxis.range[0]"]
            x_max = relayout_data["xaxis.range[1]"]
        elif "xaxis.range" in relayout_data:
            try:
                x_min, x_max = relayout_data["xaxis.range"]
            except:
                pass
        if relayout_data.get("xaxis.autorange") is True:
            x_min = x_max = None

    # If no zoom
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

    # Figure Resampler
    gc.collect()
    fig = FigureResampler(
        go.Figure(),
        default_downsampler=EveryNthPoint(),
        default_n_shown_samples=default_n_shown_samples,
    )

    y_min_global, y_max_global = None, None
    anomalous_ts, null_ts, fromto_points = [], [], []

    # =====================================================================
    # SERIES LOOP
    # =====================================================================
    for col in columnas_seleccionadas:
        col_name = col.split("::")[-1]
        if col_name not in df_plot.columns:
            continue

        y_full = df_plot[col_name].values
        y = y_full[idx_start:idx_end]

        # Eventos FROM_TO
        if col_name.endswith("-from_to"):
            base_clean = col_name.replace("-from_to", "")
            base_clean = "_".join([p for p in base_clean.split("_") if not p.startswith("Q")])

            if base_clean in df_plot.columns:
                y_base = df_plot[base_clean].values[idx_start:idx_end]
            else:
                y_base = np.zeros_like(y)

            for i, v in enumerate(y):
                if pd.isna(v) or v in (-999999, 999999):
                    continue
                try:
                    code = int(v)
                except:
                    code = None
                event_name = event_dictionary.get(code, "Evento desconocido")
                fromto_points.append((x_view[i], y_base[i], event_name, code))
            continue

        # Normal series
        anomal = (y == -999999)
        nulls = (y == 999999)
        valid = ~(anomal | nulls)

        if np.any(anomal):
            anomalous_ts.extend(x_view[anomal])
        if np.any(nulls):
            null_ts.extend(x_view[nulls])

        if np.any(valid):
            yy = y[valid]
            ymin, ymax = yy.min(), yy.max()
            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scattergl(
                    name=format_label_with_unit(columnas_info, col),
                    line=dict(width=3)
                ),
                hf_x=x_view[valid],
                hf_y=yy
            )

    # =====================================================================
    # Puntos especiales
    # =====================================================================
    base_y = (y_min_global - abs(y_min_global) * 0.05) if y_min_global is not None else 0

    # anomalous
    if anomalous_ts:
        ts = np.unique(anomalous_ts)
        fig.add_trace(
            go.Scattergl(mode="markers", marker=dict(color="orange", size=8),
                          name="Anómalo (-999999)"),
            hf_x=ts, hf_y=np.full(len(ts), base_y),
        )

    # nulls
    if null_ts:
        ts = np.unique(null_ts)
        fig.add_trace(
            go.Scattergl(mode="markers", marker=dict(color="red", size=8),
                          name="Nulo (999999)"),
            hf_x=ts, hf_y=np.full(len(ts), base_y),
        )

    # eventos from_to
    if fromto_points:
        xs = [p[0] for p in fromto_points]
        ys = [p[1] for p in fromto_points]
        cdata = [[p[2], p[3]] for p in fromto_points]

        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="blue", size=9),
                name="Eventos",
                customdata=cdata,
                hovertemplate="<b>Evento:</b> %{customdata[0]}<br>"
                              "<b>Código:</b> %{customdata[1]}<br><extra></extra>"
            ),
            hf_x=xs,
            hf_y=ys,
        )

    # =====================================================================
    # LAYOUT FINAL
    # =====================================================================
    fig.update_layout(get_graph_layout(view_min, view_max, slider_min, slider_max))
    fig.update_xaxes(
        range=[view_min, view_max],
        autorange=False,
        rangeslider=dict(visible=True, range=[slider_min, slider_max])
    )

    gc.collect()
    return fig
