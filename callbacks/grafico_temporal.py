# callbacks/grafico_temporal.py
import logging
import gc
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from plotly_resampler.aggregation import EveryNthPoint
from layouts.visuals.graph_style import get_graph_layout


# =====================================================================
# 🔥 MAPA DE EVENTOS (tu diccionario completo)
# =====================================================================
EVENT_MAP = {
    "Q05": 1,
    "Q10": 2,
    "Q20": 3,
    "Q50": 4,
    "Q90": 5,
    "Q95": 6,
    "Q05_to_Q10": 7,
    "Q05_to_Q20": 8,
    "Q05_to_Q50": 9,
    "Q05_to_Q90": 10,
    "Q05_to_Q95": 11,
    "Q10_to_Q05": 12,
    "Q10_to_Q20": 13,
    "Q10_to_Q50": 14,
    "Q10_to_Q90": 15,
    "Q10_to_Q95": 16,
    "Q20_to_Q05": 17,
    "Q20_to_Q10": 18,
    "Q20_to_Q50": 19,
    "Q20_to_Q90": 20,
    "Q20_to_Q95": 21,
    "Q50_to_Q05": 22,
    "Q50_to_Q10": 23,
    "Q50_to_Q20": 24,
    "Q50_to_Q90": 25,
    "Q50_to_Q95": 26,
    "Q90_to_Q05": 27,
    "Q90_to_Q10": 28,
    "Q90_to_Q20": 29,
    "Q90_to_Q50": 30,
    "Q90_to_Q95": 31,
    "Q95_to_Q05": 32,
    "Q95_to_Q10": 33,
    "Q95_to_Q20": 34,
    "Q95_to_Q50": 35,
    "Q95_to_Q90": 36,
    "Q05": 37,
    "Q10": 38,
    "Q20": 39,
    "Q50": 40,
    "Q90": 41,
    "Q95": 42,
    "Q05_to_Q10": 43,
    "Q05_to_Q20": 44,
    "Q05_to_Q50": 45,
    "Q05_to_Q90": 46,
    "Q05_to_Q95": 47,
    "Q10_to_Q05": 48,
    "Q10_to_Q20": 49,
    "Q10_to_Q50": 50,
    "Q10_to_Q95": 51,
    "Q20_to_Q05": 52,
    "Q20_to_Q10": 53,
    "Q20_to_Q50": 54,
    "Q20_to_Q90": 55,
    "Q20_to_Q95": 56,
    "Q50_to_Q05": 57,
    "Q50_to_Q10": 58,
    "Q50_to_Q20": 59,
    "Q50_to_Q90": 60,
    "Q50_to_Q95": 61,
    "Q90_to_Q05": 62,
    "Q90_to_Q20": 63,
    "Q90_to_Q50": 64,
    "Q90_to_Q95": 65,
    "Q95_to_Q05": 66,
    "Q95_to_Q10": 67,
    "Q95_to_Q20": 68,
    "Q95_to_Q50": 69,
    "Q95_to_Q90": 70,
    "Q05": 71,
    "Q10": 72,
    "Q20": 73,
    "Q50": 74,
    "Q90": 75,
    "Q95": 76,
    "Q05_to_Q10": 77,
    "Q05_to_Q20": 78,
    "Q05_to_Q50": 79,
    "Q05_to_Q95": 80,
    "Q10_to_Q05": 81,
    "Q10_to_Q20": 82,
    "Q10_to_Q50": 83,
    "Q20_to_Q05": 84,
    "Q20_to_Q10": 85,
    "Q20_to_Q50": 86,
    "Q20_to_Q90": 87,
    "Q20_to_Q95": 88,
    "Q50_to_Q05": 89,
    "Q50_to_Q10": 90,
    "Q50_to_Q20": 91,
    "Q50_to_Q90": 92,
    "Q50_to_Q95": 93,
    "Q90_to_Q10": 94,
    "Q90_to_Q20": 95,
    "Q90_to_Q50": 96,
    "Q90_to_Q95": 97,
    "Q95_to_Q20": 98,
    "Q95_to_Q50": 99,
    "Q95_to_Q90": 100,
    "Q05": 101,
    "Q20": 102,
    "Q50": 103,
    "Q95": 104,
    "Q05_to_Q20": 105,
    "Q05_to_Q50": 106,
    "Q05_to_Q95": 107,
    "Q20_to_Q05": 108,
    "Q20_to_Q50": 109,
    "Q20_to_Q95": 110,
    "Q50_to_Q05": 111,
    "Q50_to_Q20": 112,
    "Q50_to_Q95": 113,
    "Q95_to_Q05": 114,
    "Q95_to_Q20": 115,
    "Q95_to_Q50": 116,
    "Q05": 117,
    "Q50": 118,
    "Q90": 119,
    "Q95": 120,
    "Q05_to_Q50": 121,
    "Q50_to_Q05": 122,
    "Q50_to_Q90": 123,
    "Q50_to_Q95": 124,
    "Q90_to_Q05": 125,
    "Q90_to_Q50": 126,
    "Q90_to_Q95": 127,
    "Q95_to_Q05": 128,
    "Q95_to_Q50": 129,
    "Q95_to_Q90": 130,
    "Q05": 131,
    "Q10": 132,
    "Q20": 133,
    "Q50": 134,
    "Q95": 135,
    "Q05_to_Q10": 136,
    "Q05_to_Q20": 137,
    "Q05_to_Q50": 138,
    "Q10_to_Q05": 139,
    "Q10_to_Q20": 140,
    "Q10_to_Q50": 141,
    "Q10_to_Q95": 142,
    "Q20_to_Q05": 143,
    "Q20_to_Q10": 144,
    "Q20_to_Q50": 145,
    "Q20_to_Q95": 146,
    "Q50_to_Q05": 147,
    "Q50_to_Q10": 148,
    "Q50_to_Q20": 149,
    "Q50_to_Q95": 150,
    "Q95_to_Q05": 151,
    "Q95_to_Q10": 152,
    "Q95_to_Q20": 153,
    "Q95_to_Q50": 154
}



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

    gc.collect()

    # ---------------------------------------------------------------------
    # 0. Sin columnas seleccionadas
    # ---------------------------------------------------------------------
    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Selecciona al menos una serie.")

    # ---------------------------------------------------------------------
    # 1. Rango absoluto del slider
    # ---------------------------------------------------------------------
    if slider_data:
        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])
    else:
        tmp = pd.to_datetime(df_plot[x_timer])
        slider_min, slider_max = tmp.iloc[0], tmp.iloc[-1]

    full_x = df_plot[x_timer].values

    # ---------------------------------------------------------------------
    # 2. Procesar zoom/slider
    # ---------------------------------------------------------------------
    x_min, x_max = None, None

    if relayout_data:

        # Zoom manual
        if "xaxis.range[0]" in relayout_data:
            x_min = relayout_data["xaxis.range[0]"]
            x_max = relayout_data["xaxis.range[1]"]

        # Movimiento del slider
        elif "xaxis.range" in relayout_data:
            try:
                x_min, x_max = relayout_data["xaxis.range"]
            except:
                pass

        if relayout_data.get("xaxis.autorange") is True:
            x_min = x_max = None

    # ---------------------------------------------------------------------
    # 3. Slicing
    # ---------------------------------------------------------------------
    if x_min is None or x_max is None:
        idx_start = 0
        idx_end = len(full_x)
        view_min, view_max = slider_min, slider_max
    else:
        tmin = pd.to_datetime(x_min).to_datetime64()
        tmax = pd.to_datetime(x_max).to_datetime64()

        idx_start = np.searchsorted(full_x, tmin)
        idx_end = np.searchsorted(full_x, tmax)

        idx_start = max(0, idx_start)
        idx_end = min(len(full_x), idx_end)

        view_min, view_max = x_min, x_max

    if idx_end <= idx_start:
        idx_start, idx_end = 0, len(full_x)
        view_min, view_max = slider_min, slider_max

    x_view = full_x[idx_start:idx_end]

    # ---------------------------------------------------------------------
    # 4. Figura resampler
    # ---------------------------------------------------------------------
    fig = FigureResampler(
        go.Figure(),
        default_downsampler=EveryNthPoint(),
        default_n_shown_samples=default_n_shown_samples,
    )

    y_min_global = None
    y_max_global = None

    # ---------------------------------------------------------------------
    # 5. Detección: anomalías, nulos, from_to
    # ---------------------------------------------------------------------
    anomalous_ts = []
    null_ts = []
    fromto_points = []  # (x, y, eventID)

    for col in columnas_seleccionadas:

        col_name = col.split("::")[-1]

        if col_name not in df_plot.columns:
            continue

        y_full = df_plot[col_name].values
        y = y_full[idx_start:idx_end]

        if len(y) == 0:
            continue

        # ---------------------------------------------------------------
        # A) FROM_TO — puntos colocados a la altura de la columna base
        # ---------------------------------------------------------------
        if col_name.endswith("-from_to"):

            col_base = col_name.replace("-from_to", "")

            if col_base in df_plot.columns:

                y_base_values = df_plot[col_base].values[idx_start:idx_end]
                event_id = EVENT_MAP.get(col_name, None)

                for i, v in enumerate(y):

                    if np.isnan(v) or v in (-999999, 999999):
                        continue

                    fromto_points.append(
                        (x_view[i], y_base_values[i], event_id)
                    )

            continue  # No se dibuja línea

        # ---------------------------------------------------------------
        # B) ANÓMALOS / NULOS
        # ---------------------------------------------------------------
        is_anomaly = (y == -999999.0)
        is_null = (y == 999999.0)
        is_invalid = is_anomaly | is_null

        if np.any(is_anomaly):
            anomalous_ts.extend(x_view[is_anomaly])

        if np.any(is_null):
            null_ts.extend(x_view[is_null])

        # ---------------------------------------------------------------
        # C) Valores válidos → línea normal
        # ---------------------------------------------------------------
        is_valid = ~(is_invalid) & (y > -999998.0) & (y < 999998.0)

        if np.any(is_valid):

            yy = y[is_valid]
            ymin, ymax = np.min(yy), np.max(yy)

            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scattergl(   
                    # name=format_label_with_unit(col),
                    name=format_label_with_unit(columnas_info, col),
                    line=dict(width=3)
                ),
                hf_x=x_view[is_valid],
                hf_y=yy,
            )

    # ---------------------------------------------------------------------
    # 5D. Dibujar anomalías/nulos
    # ---------------------------------------------------------------------
    base_y = 0 if y_min_global is None else y_min_global - abs(y_min_global) * 0.05

    # Anómalos
    if anomalous_ts:
        ts = np.unique(anomalous_ts)
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="orange", size=8),
                name="Anómalo (-999999)"
            ),
            hf_x=ts,
            hf_y=np.full(len(ts), base_y),
        )

    # Nulos
    if null_ts:
        ts = np.unique(null_ts)
        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="red", size=8),
                name="Nulo (999999)"
            ),
            hf_x=ts,
            hf_y=np.full(len(ts), base_y),
        )

    # ---------------------------------------------------------------------
    # 5E. Dibujar from_to (rápido, solo eventID)
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # 5E. Dibujar from_to (rápido, solo eventID)
    # ---------------------------------------------------------------------
    if fromto_points:

        xs = [p[0] for p in fromto_points]
        ys = [p[1] for p in fromto_points]

        # p[2] = eventID, si no existe, poner '-'
        texts = [f"{p[2]}" if p[2] is not None else "-" for p in fromto_points]

        fig.add_trace(
            go.Scattergl(
                mode="markers",
                marker=dict(color="blue", size=9),
                name="from_to",
                hovertemplate="Evento %{text}<extra></extra>",
                text=texts,
            ),
            hf_x=xs,   # ✔ obligatorio para Resampler
            hf_y=ys,   # ✔ obligatorio para Resampler
        )

    # ---------------------------------------------------------------------
    # 6. Layout
    # ---------------------------------------------------------------------
    fig.update_layout(
        get_graph_layout(view_min, view_max, slider_min, slider_max)
    )

    # ---------------------------------------------------------------------
    # 7. Slider fijo
    # ---------------------------------------------------------------------
    fig.update_xaxes(
        range=[view_min, view_max],
        autorange=False,
        rangeslider=dict(visible=True, range=[slider_min, slider_max])
    )

    return fig
