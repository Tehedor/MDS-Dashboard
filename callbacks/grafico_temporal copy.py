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
# 🔥 NUEVO MAPA DE EVENTOS (invertido: código → nombre)
# =====================================================================
EVENT_MAP = {
    1: "Q05", 2: "Q10", 3: "Q20", 4: "Q50", 5: "Q90", 6: "Q95",
    7: "Q05_to_Q10", 8: "Q05_to_Q20", 9: "Q05_to_Q50", 10: "Q05_to_Q90", 11: "Q05_to_Q95",
    12: "Q10_to_Q05", 13: "Q10_to_Q20", 14: "Q10_to_Q50", 15: "Q10_to_Q90", 16: "Q10_to_Q95",
    17: "Q20_to_Q05", 18: "Q20_to_Q10", 19: "Q20_to_Q50", 20: "Q20_to_Q90", 21: "Q20_to_Q95",
    22: "Q50_to_Q05", 23: "Q50_to_Q10", 24: "Q50_to_Q20", 25: "Q50_to_Q90", 26: "Q50_to_Q95",
    27: "Q90_to_Q05", 28: "Q90_to_Q10", 29: "Q90_to_Q20", 30: "Q90_to_Q50", 31: "Q90_to_Q95",
    32: "Q95_to_Q05", 33: "Q95_to_Q10", 34: "Q95_to_Q20", 35: "Q95_to_Q50", 36: "Q95_to_Q90",
    37: "Q05", 38: "Q10", 39: "Q20", 40: "Q50", 41: "Q90", 42: "Q95",
    43: "Q05_to_Q10", 44: "Q05_to_Q20", 45: "Q05_to_Q50", 46: "Q05_to_Q90", 47: "Q05_to_Q95",
    48: "Q10_to_Q05", 49: "Q10_to_Q20", 50: "Q10_to_Q50", 51: "Q10_to_Q95",
    52: "Q20_to_Q05", 53: "Q20_to_Q10", 54: "Q20_to_Q50", 55: "Q20_to_Q90", 56: "Q20_to_Q95",
    57: "Q50_to_Q05", 58: "Q50_to_Q10", 59: "Q50_to_Q20", 60: "Q50_to_Q90", 61: "Q50_to_Q95",
    62: "Q90_to_Q05", 63: "Q90_to_Q20", 64: "Q90_to_Q50", 65: "Q90_to_Q95",
    66: "Q95_to_Q05", 67: "Q95_to_Q10", 68: "Q95_to_Q20", 69: "Q95_to_Q50", 70: "Q95_to_Q90",
    71: "Q05", 72: "Q10", 73: "Q20", 74: "Q50", 75: "Q90", 76: "Q95",
    77: "Q05_to_Q10", 78: "Q05_to_Q20", 79: "Q05_to_Q50", 80: "Q05_to_Q95",
    81: "Q10_to_Q05", 82: "Q10_to_Q20", 83: "Q10_to_Q50",
    84: "Q20_to_Q05", 85: "Q20_to_Q10", 86: "Q20_to_Q50", 87: "Q20_to_Q90", 88: "Q20_to_Q95",
    89: "Q50_to_Q05", 90: "Q50_to_Q10", 91: "Q50_to_Q20", 92: "Q50_to_Q90", 93: "Q50_to_Q95",
    94: "Q90_to_Q10", 95: "Q90_to_Q20", 96: "Q90_to_Q50", 97: "Q90_to_Q95",
    98: "Q95_to_Q20", 99: "Q95_to_Q50", 100: "Q95_to_Q90",
    101: "Q05", 102: "Q20", 103: "Q50", 104: "Q95",
    105: "Q05_to_Q20", 106: "Q05_to_Q50", 107: "Q05_to_Q95",
    108: "Q20_to_Q05", 109: "Q20_to_Q50", 110: "Q20_to_Q95",
    111: "Q50_to_Q05", 112: "Q50_to_Q20", 113: "Q50_to_Q95",
    114: "Q95_to_Q05", 115: "Q95_to_Q20", 116: "Q95_to_Q50",
    117: "Q05", 118: "Q50", 119: "Q90", 120: "Q95",
    121: "Q05_to_Q50", 122: "Q50_to_Q05", 123: "Q50_to_Q90", 124: "Q50_to_Q95",
    125: "Q90_to_Q05", 126: "Q90_to_Q50", 127: "Q90_to_Q95",
    128: "Q95_to_Q05", 129: "Q95_to_Q50", 130: "Q95_to_Q90",
    131: "Q05", 132: "Q10", 133: "Q20", 134: "Q50", 135: "Q95",
    136: "Q05_to_Q10", 137: "Q05_to_Q20", 138: "Q05_to_Q50",
    139: "Q10_to_Q05", 140: "Q10_to_Q20", 141: "Q10_to_Q50", 142: "Q10_to_Q95",
    143: "Q20_to_Q05", 144: "Q20_to_Q10", 145: "Q20_to_Q50", 146: "Q20_to_Q95",
    147: "Q50_to_Q05", 148: "Q50_to_Q10", 149: "Q50_to_Q20", 150: "Q50_to_Q95",
    151: "Q95_to_Q05", 152: "Q95_to_Q10", 153: "Q95_to_Q20", 154: "Q95_to_Q50"
}

# =====================================================================
# 🔄 ACTUALIZAR GRÁFICO COMPATIBLE CON EVENT_MAP INVERTIDO
# =====================================================================
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

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Selecciona al menos una serie.")

    # ===== SLIDER RANGE =====
    if slider_data:
        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])
    else:
        tmp = pd.to_datetime(df_plot[x_timer])
        slider_min, slider_max = tmp.iloc[0], tmp.iloc[-1]

    full_x = df_plot[x_timer].values

    # ===== ZOOM / PAN =====
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

    if x_min is None or x_max is None:
        idx_start = 0
        idx_end = len(full_x)
        view_min, view_max = slider_min, slider_max
    else:
        tmin = pd.to_datetime(x_min).to_datetime64()
        tmax = pd.to_datetime(x_max).to_datetime64()
        idx_start = max(0, np.searchsorted(full_x, tmin))
        idx_end = min(len(full_x), np.searchsorted(full_x, tmax))
        view_min, view_max = x_min, x_max

    x_view = full_x[idx_start:idx_end]

    # ===== FIGURE RESAMPLER =====
    fig = FigureResampler(
        go.Figure(),
        default_downsampler=EveryNthPoint(),
        default_n_shown_samples=default_n_shown_samples,
    )

    y_min_global, y_max_global = None, None
    anomalous_ts, null_ts, fromto_points = [], [], []

    # =====================================================================
    # 🔍 RECORRER SERIES
    # =====================================================================
    for col in columnas_seleccionadas:

        col_name = col.split("::")[-1]
        if col_name not in df_plot.columns:
            continue

        y_full = df_plot[col_name].values
        y = y_full[idx_start:idx_end]

        # ============================
        # 🔵 EVENTOS (FROM_TO)
        # ============================
        if col_name.endswith("-from_to"):

            # Columna base ( Battery_Active_Power_Q05_to_Q10-from_to → Battery_Active_Power )
            clean = col_name.replace("-from_to", "")
            parts = clean.split("_")
            # eliminación de Qxx o Qxx_to_Qyy
            parts = [p for p in parts if not p.startswith("Q")]
            col_base = "_".join(parts)

            if col_base in df_plot.columns:
                y_base = df_plot[col_base].values[idx_start:idx_end]
            else:
                y_base = np.zeros_like(y)

            # Procesar cada código
            for i, v in enumerate(y):
                if pd.isna(v) or v in (-999999, 999999):
                    continue

                try:
                    code = int(v)
                except:
                    code = None

                event_name = EVENT_MAP.get(code, "Evento desconocido")

                fromto_points.append(
                    (x_view[i], y_base[i], event_name, code)
                )

            continue  # Saltamos dibujar línea

        # ============================
        # 📈 SERIES NORMALES
        # ============================
        is_anomaly = (y == -999999)
        is_null = (y == 999999)
        is_valid = ~(is_anomaly | is_null)

        anomalous_ts.extend(x_view[is_anomaly])
        null_ts.extend(x_view[is_null])

        if np.any(is_valid):
            yy = y[is_valid]

            ymin, ymax = yy.min(), yy.max()
            y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
            y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scattergl(name=format_label_with_unit(columnas_info, col), line=dict(width=3)),
                hf_x=x_view[is_valid],
                hf_y=yy
            )

    # =====================================================================
    # 🔴 DIBUJO DE PUNTOS ESPECIALES
    # =====================================================================
    base_y = (y_min_global - abs(y_min_global) * 0.05) if y_min_global is not None else 0

    # ANÓMALOS
    if anomalous_ts:
        ts = np.unique(anomalous_ts)
        fig.add_trace(
            go.Scattergl(mode="markers", marker=dict(color="orange", size=8), name="Anómalo (-999999)"),
            hf_x=ts, hf_y=np.full(len(ts), base_y),
        )

    # NULOS
    if null_ts:
        ts = np.unique(null_ts)
        fig.add_trace(
            go.Scattergl(mode="markers", marker=dict(color="red", size=8), name="Nulo (999999)"),
            hf_x=ts, hf_y=np.full(len(ts), base_y),
        )

    # EVENTOS FROM_TO
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
                              "<b>Código:</b> %{customdata[1]}<br>"
                              "<extra></extra>"
            ),
            hf_x=xs,
            hf_y=ys,
        )

    # =====================================================================
    # 🧩 LAYOUT FINAL
    # =====================================================================
    fig.update_layout(get_graph_layout(view_min, view_max, slider_min, slider_max))
    fig.update_xaxes(
        range=[view_min, view_max],
        autorange=False,
        rangeslider=dict(visible=True, range=[slider_min, slider_max])
    )

    return fig
