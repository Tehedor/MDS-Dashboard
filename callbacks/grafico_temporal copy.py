# callbacks/grafico_temporal.py
import logging
import pandas as pd
import plotly.graph_objects as go
from plotly_resampler import FigureResampler
from layouts.visuals.graph_style import get_graph_layout


# ----------------------------------------------------------
# Interpretar valores del checklist
# ----------------------------------------------------------
def parse_column_value(value):
    if "::" in value:
        comp, mode, name = value.split("::", 2)
        return {"type": mode, "component": comp, "name": name}
    return {"type": "tabular", "component": None, "name": value}



# ----------------------------------------------------------
# Construir serie binaria para eventos
# ----------------------------------------------------------
def get_event_series(df, event_type, codes):
    colname = "events_state" if event_type == "raw" else "events_from_to"
    if colname not in df:
        return None

    col = df[colname]
    mask = col.apply(lambda lista: any(c in lista for c in codes) if isinstance(lista, list) else False)
    return mask.astype(int)



# ----------------------------------------------------------
# Buscar códigos del evento en columnas_info
# ----------------------------------------------------------
def _buscar_event_codes(item_name, component, mode, columnas_info):

    for item in columnas_info:

        if item.get("type") != mode:
            continue

        if item.get("component") != component:
            continue

        # MATCH POR NOMBRE COMPLETO o POR measurement
        if item.get("name") == item_name or item.get("measurement") == item_name:
            return item.get("codes")

    return None



# ----------------------------------------------------------
# Renderizar la figura
# ----------------------------------------------------------
def actualizar_grafico(
    columnas_seleccionadas,
    relayout_data,
    df_plot,
    x_timer,
    format_label_with_unit,
    columnas_info,
    default_n_shown_samples=500,
):

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Selecciona una serie")

    df_visible = df_plot

    fig = FigureResampler(go.Figure(), default_n_shown_samples)

    y_min_global, y_max_global = None, None

    for val in columnas_seleccionadas:

        info = parse_column_value(val)
        col_type = info["type"]
        col_name = info["name"]
        comp = info["component"]

        etiqueta = col_name if col_type != "tabular" else format_label_with_unit(col_name)

        # ----------------------------------------------------------
        # TABULAR
        # ----------------------------------------------------------
        if col_type == "tabular":

            if col_name not in df_visible:
                continue

            serie = df_visible[[x_timer, col_name]]
            validos = serie[serie[col_name].between(-999998, 999998)]

            if not validos.empty:
                ymin = validos[col_name].min()
                ymax = validos[col_name].max()
                y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
                y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scatter(name=etiqueta, mode="lines"),
                hf_x=validos[x_timer],
                hf_y=validos[col_name]
            )
            continue

        # ----------------------------------------------------------
        # EVENTOS
        # ----------------------------------------------------------
        codes = _buscar_event_codes(col_name, comp, col_type, columnas_info)
        if not codes:
            continue

        serie_event = get_event_series(df_visible, col_type, codes)
        if serie_event is None:
            continue

        y_min_global = 0 if y_min_global is None else min(y_min_global, 0)
        y_max_global = 1 if y_max_global is None else max(y_max_global, 1)

        fig.add_trace(
            go.Scatter(name=etiqueta, mode="lines"),
            hf_x=df_visible[x_timer],
            hf_y=serie_event
        )

    # ----------------------------------------------------------
    # Layout final
    # ----------------------------------------------------------
    try:
        fig.update_layout(get_graph_layout(None, None, df_plot[x_timer].min(), df_plot[x_timer].max()))
    except:
        fig.update_layout(title="Gráfico temporal")

    return fig
