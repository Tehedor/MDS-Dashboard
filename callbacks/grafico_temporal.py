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
#                 FUNCIÓN PRINCIPAL DEL GRÁFICO
# ==========================================================
def actualizar_grafico(
    columnas_seleccionadas,
    relayout_data,
    df_plot,
    x_timer,
    format_label_with_unit,
    columnas_info,
    default_n_shown_samples=600,
):

    logging.info(f"↪ Ejecutando gráfico. Columnas: {columnas_seleccionadas}")

    if not columnas_seleccionadas:
        return go.Figure().update_layout(title="Selecciona una serie")

    # Convertimos X a datetime si hace falta
    if not pd.api.types.is_datetime64_any_dtype(df_plot[x_timer]):
        df_plot = df_plot.copy()
        df_plot[x_timer] = pd.to_datetime(df_plot[x_timer])

    # ----------------------------------------------------------
    # 1) Leer el zoom si existe
    # ----------------------------------------------------------
    x_min, x_max = None, None

    if relayout_data:
        if "xaxis.range[0]" in relayout_data and "xaxis.range[1]" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range[0]"])
            x_max = pd.to_datetime(relayout_data["xaxis.range[1]"])
        elif "xaxis.range" in relayout_data:
            x_min = pd.to_datetime(relayout_data["xaxis.range"][0])
            x_max = pd.to_datetime(relayout_data["xaxis.range"][1])
        elif "xaxis.autorange" in relayout_data:
            x_min, x_max = None, None

    # ----------------------------------------------------------
    # 2) Filtrar por zoom
    # ----------------------------------------------------------
    df_visible = df_plot if x_min is None else df_plot[
        (df_plot[x_timer] >= x_min) & (df_plot[x_timer] <= x_max)
    ]

    # ----------------------------------------------------------
    # 3) Crear figura
    # ----------------------------------------------------------
    fig = FigureResampler(go.Figure(), default_n_shown_samples=default_n_shown_samples)

    y_min_global, y_max_global = None, None

    # ==========================================================
    # 4) Procesar cada columna seleccionada
    # ==========================================================
    for val in columnas_seleccionadas:

        info = parse_column_value(val)
        col_type = info["type"]
        col_name = info["name"]
        comp = info["component"]

        etiqueta = col_name if col_type != "tabular" else format_label_with_unit(col_name)

        # ======================================================
        #                TABULAR (curvas normales)
        # ======================================================
        if col_type == "tabular":

            if col_name not in df_visible:
                continue

            serie = df_visible[[x_timer, col_name]]
            serie_validos = serie[serie[col_name].between(-999998, 999998)]

            if not serie_validos.empty:
                ymin = serie_validos[col_name].min()
                ymax = serie_validos[col_name].max()
                y_min_global = ymin if y_min_global is None else min(y_min_global, ymin)
                y_max_global = ymax if y_max_global is None else max(y_max_global, ymax)

            fig.add_trace(
                go.Scatter(name=etiqueta, mode="lines", line=dict(width=2)),
                hf_x=serie_validos[x_timer],
                hf_y=serie_validos[col_name]
            )
            continue

        # ======================================================
        #                  EVENTOS RAW (0/1)
        # ======================================================
        if col_type == "raw":

            codes = _buscar_event_codes(col_name, comp, "raw", columnas_info)
            if not codes:
                continue

            serie_event = get_event_series(df_visible, "raw", codes)
            if serie_event is None:
                continue

            # evento raw siempre es 0/1
            fig.add_trace(
                go.Scatter(name=f"{etiqueta} (raw)", mode="lines", line=dict(width=1.5, dash="dot")),
                hf_x=df_visible[x_timer],
                hf_y=serie_event
            )
            continue

        # ======================================================
        #                EVENTOS FROM_TO (PUNTOS)
        # ======================================================

        if col_type == "from_to":
            logging.info(f"@@2@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            logging.info(f"Procesando columna eventos from_to: {col_name} (componente: {comp})")
            logging.info(f"@@2@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            # Recuperar measurement correcto
            full_name = info["name"]   # ej: "Battery_Active_Power_from_to"
            tabular_name = full_name.replace("_from_to", "")

            codes = _buscar_event_codes(full_name, comp, "from_to", columnas_info)
            if not codes:
                continue

            if tabular_name not in df_visible:
                continue

            col_event_name = f"{tabular_name}_from_to"


            if col_event_name not in df_visible:
                # DEBUG → No existe la columna from_to
                save_debug_info(
                    {
                        "error": "columna_from_to_no_existe",
                        "col_event_name": col_event_name,
                        "df_cols": list(df_visible.columns),
                    },
                    filename="debug_fromto_missing_column",
                    # directory=Path("./debug")
                )
                continue

            serie_event = df_visible[col_event_name]
            serie_tab = df_visible[tabular_name]

            mask = serie_event.notna()

            # --------------------------------------------------
            # 🔥 DEBUG → GUARDAR INFORMACIÓN DETALLADA
            # --------------------------------------------------
            debug_payload = {
                "col_type": col_type,
                "col_name": col_name,
                "component": comp,
                "tabular_name": tabular_name,
                "col_event_name": col_event_name,
                "codes_expected": codes,
                "num_rows_df_visible": len(df_visible),
                "num_rows_event_notna": int(mask.sum()),
                "mask_first_20": mask.head(20).tolist(),
                "event_values_first_20": serie_event.head(20).astype(str).tolist(),
                "tab_values_first_20": serie_tab.head(20).astype(str).tolist(),
            }

            save_debug_info(
                debug_payload,
                filename=f"debug_fromto_{col_name}",
                # directory=Path("./debug")
            )
            # --------------------------------------------------

            # Si no hay eventos → continuar
            if not mask.any():
                continue

            eventos_x = df_visible.loc[mask, x_timer]
            eventos_y = df_visible.loc[mask, tabular_name]
            eventos_codigo = serie_event.loc[mask]

            fig.add_trace(
                go.Scatter(
                    x=eventos_x,
                    y=eventos_y,
                    mode="markers",
                    name=f"{etiqueta} (eventos)",
                    marker=dict(size=12, color="red", symbol="diamond"),
                    text=[
                        f"<b>Evento:</b> {etiqueta}<br>"
                        f"<b>Código:</b> {float(c)}<br>"
                        f"<b>Valor Y:</b> {float(v):.3f}"
                        for c, v in zip(eventos_codigo, eventos_y)
                    ],
                    hovertemplate="%{text}<extra></extra>"
                )
            )


            # Expandir rango Y
            y_min_global = (
                eventos_y.min()
                if y_min_global is None else min(y_min_global, eventos_y.min())
            )
            y_max_global = (
                eventos_y.max()
                if y_max_global is None else max(y_max_global, eventos_y.max())
            )

            continue


    # ----------------------------------------------------------
    # 5) Layout final
    # ----------------------------------------------------------
    slider_min = df_plot[x_timer].min()
    slider_max = df_plot[x_timer].max()

    fig.update_layout(
        get_graph_layout(
            x_min,
            x_max,
            slider_min,
            slider_max
        )
    )

    return fig
