import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout
from debug.debug import save_debug_info

# ----------------------------------------------------------
# Interpretar value del checklist (tabular / raw / from_to)
# ----------------------------------------------------------
def parse_column_value(value):
    if "::" in value:
        comp, mode, name = value.split("::", 2)
        return {"type": mode, "component": comp, "name": name}
    return {"type": "tabular", "component": None, "name": value}


# ----------------------------------------------------------
# EVENTOS tipo RAW: presencia (0/1)
# ----------------------------------------------------------
def get_event_series(df, event_type, codes):
    colname = "events_state" if event_type == "raw" else "events_from_to"
    if colname not in df:
        return None

    col = df[colname]
    mask = col.apply(lambda lista: any(c in lista for c in codes) if isinstance(lista, list) else False)
    return mask.astype(int)


# ----------------------------------------------------------
# Buscar códigos desde metadata
# ----------------------------------------------------------
def _buscar_event_codes(item_name, comp, mode, columnas_info):
    for item in columnas_info:
        if item.get("type") != mode:
            continue
        if item.get("component") != comp:
            continue
        if item.get("name") == item_name or item.get("measurement") == item_name:
            return item.get("codes")
    return None


# ==========================================================
#           FUNCIÓN PRINCIPAL DEL GRÁFICO (OPTIMIZADA)
# ==========================================================
def actualizar_grafico(
    columnas_seleccionadas,
    relayout_data,
    df_plot,
    x_timer,                     # ignorado
    format_label_with_unit,
    columnas_info,
    default_n_shown_samples=600,
):

    logging.info(f"↪ Ejecutando gráfico. Columnas seleccionadas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Selecciona una serie")

    # ----------------------------------------------------------
    # 0) df_plot YA VIENE con índice datetime y ORDENADO
    # ----------------------------------------------------------
    # ⚠️ NO copiar, NO convertir el índice → evitar cuellos de botella
    df = df_plot

    # ----------------------------------------------------------
    # 1) Leer rango de zoom
    # ----------------------------------------------------------
    x_min, x_max = None, None
    if relayout_data:
        if "xaxis.range[0]" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range[0]"])
            x_max = pd.to_datetime(relayout_data["xaxis.range[1]"])
        elif "xaxis.range" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range"][0])
            x_max = pd.to_datetime(relayout_data["xaxis.range"][1])
        elif "xaxis.autorange" in relayout_data:
            x_min, x_max = None, None

    # ----------------------------------------------------------
    # 2) Aplicar zoom rápido → .loc solo es O(log n) si index está ordenado
    # ----------------------------------------------------------
    if x_min is None:
        df_visible = df
    else:
        df_visible = df.loc[x_min:x_max]

    # ----------------------------------------------------------
    # 3) Crear figura resampleada
    # ----------------------------------------------------------
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    # ==========================================================
    # 4) Procesar columnas
    # ==========================================================
    for val in columnas_seleccionadas:

        info = parse_column_value(val)
        col_type = info["type"]
        col_name = info["name"]
        comp = info["component"]

        etiqueta = col_name if col_type != "tabular" else format_label_with_unit(col_name)

        # ======================================================
        # TABULAR
        # ======================================================
        if col_type == "tabular":

            if col_name not in df_visible:
                continue

            values = df_visible[col_name]

            # añadir traza resampleada
            fig.add_trace(
                go.Scatter(name=etiqueta, mode="lines", line=dict(width=2)),
                hf_x=values.index,
                hf_y=values,
            )
            continue

        # ======================================================
        # EVENTOS RAW (0/1)
        # ======================================================
        if col_type == "raw":

            codes = _buscar_event_codes(col_name, comp, "raw", columnas_info)
            if not codes:
                continue

            serie_event = get_event_series(df_visible, "raw", codes)
            if serie_event is None:
                continue

            fig.add_trace(
                go.Scatter(
                    name=f"{etiqueta} (raw)",
                    mode="lines",
                    line=dict(width=1.5, dash="dot")
                ),
                hf_x=df_visible.index,
                hf_y=serie_event,
            )
            continue

        # ======================================================
        # EVENTOS FROM_TO
        # ======================================================
        if col_type == "from_to":

            base_name = col_name.replace("_from_to", "")
            event_col = f"{base_name}_from_to"

            if base_name not in df_visible or event_col not in df_visible:
                continue

            serie_event = df_visible[event_col]
            serie_tab = df_visible[base_name]

            mask = serie_event.notna()

            if not mask.any():
                continue

            eventos_x = df_visible.index[mask]
            eventos_y = serie_tab[mask]
            eventos_cod = serie_event[mask]

            fig.add_trace(
                go.Scatter(
                    x=eventos_x,
                    y=eventos_y,
                    mode="markers",
                    name=f"{etiqueta} (eventos)",
                    marker=dict(size=10, color="red", symbol="diamond"),
                    text=[
                        f"<b>Evento:</b> {etiqueta}<br>"
                        f"<b>Código:</b> {float(c)}<br>"
                        f"<b>Valor:</b> {float(v):.3f}"
                        for c, v in zip(eventos_cod, eventos_y)
                    ],
                    hovertemplate="%{text}<extra></extra>"
                )
            )

    # ----------------------------------------------------------
    # 5) Configurar layout final (slider)
    # ----------------------------------------------------------
    fig.update_layout(
        get_graph_layout(
            x_min,
            x_max,
            df.index.min(),
            df.index.max(),
        )
    )

    return fig
