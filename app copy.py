# app.py
# =====================================================
# app.py — versión con integración de event_dictionary y gestión de memoria
# =====================================================

import dash
import logging
import os
import gc
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd

from utils.dataset.DatasetRegistry import DatasetRegistry
from utils.cache_config import init_cache, cache_config, limpiar_cache
from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico
from debug.debug import save_debug_info
from utils.helpers import format_label_with_unit, build_checklist_options

# -----------------------------------------------------
# LOGGING
# -----------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# -----------------------------------------------------
# CARGA DATASETS
# -----------------------------------------------------
BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"
registry = DatasetRegistry(BASE_DATASETS_DIR)

datasets_disponibles = registry.list()
if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles!")

# -----------------------------------------------------
# APP + CACHE
# -----------------------------------------------------
app = dash.Dash(__name__)
cache = init_cache(app)
cache_config(cache)
server = app.server

# DF + METADATA EN MEMORIA
MAPA_DF = {}

# =====================================================
# LAYOUT
# =====================================================
def get_layout():
    return html.Div([
        dcc.Store(id="current-config"),
        dcc.Store(id="current-components"),
        dcc.Store(id="current-columns"),
        dcc.Store(id="cached-df"),
        dcc.Store(id="slider-absolute-range"),
        dcc.Store(id="initial-figure-store"),

        serve_layout(
            config={},
            datasets=datasets_disponibles,
            opciones_checklist=[],
            columnas=[],
            x_timer="Timestamp",
            default_dataset=datasets_disponibles[0],
        ),
    ])

app.layout = get_layout


# =====================================================
# CALLBACK — CARGA DATASET
# =====================================================
@app.callback(
    [
        Output("current-config", "data"),
        Output("current-components", "data"),
        Output("current-columns", "data"),
        Output("cached-df", "data"),
        Output("slider-absolute-range", "data"),
    ],
    Input("dataset-selector", "value")
)
def cargar_dataset(dataset_name):
    log.info(f"➡ Cargando dataset {dataset_name}...")

    # LIMPIAR caché y mapa antes de cargar el nuevo dataset para evitar OOM
    try:
        limpiar_cache(cache)
    except Exception as e:
        log.warning(f"No se pudo limpiar la caché antes de cargar dataset: {e}")

    MAPA_DF.clear()
    gc.collect()

    ds = registry.get(dataset_name)
    cfg = ds.main.config if hasattr(ds, "main") else {}

    cols_info = ds.get_all_columns()
    components_meta = cols_info.get("components_meta", {})
    all_columns = cols_info.get("all", [])

    # Guardamos metadata global
    MAPA_DF["components_meta"] = components_meta

    # =======================================================
    # 🔥 capturar event_dictionary del subdataset evento
    # =======================================================
    event_dictionary = {}
    for sd in ds.secondary.values():
        if sd.type.lower() == "eventencodeddataset":
            # sd.event_dictionary fue generado en SubDataset.build_event_dictionary()
            event_dictionary = getattr(sd, "event_dictionary", {}) or {}
            break

    MAPA_DF["event_dictionary"] = event_dictionary

    # Debug opcional
    # save_debug_info(
    #     content_source=cols_info,
    #     filename=f"colls_info_{dataset_name}",
    #     head=f"HEADER DE cols_info para dataset '{dataset_name}': {ds.name}"
    # )

    # ---------------------------------------------------------
    # Evitar copia masiva del DataFrame (no hacer df.copy() aquí)
    # ---------------------------------------------------------
    df = ds.df
    MAPA_DF["actual"] = df

    # Asegurarse de que Timestamp existe y está ordenado
    if "Timestamp" not in df.columns:
        # si no existe, intentar crear desde índice
        try:
            df["Timestamp"] = df.index
        except Exception:
            pass

    slider_range = {
        "min": pd.to_datetime(df["Timestamp"].iloc[0]),
        "max": pd.to_datetime(df["Timestamp"].iloc[-1])
    }

    # Forzar GC antes de devolver
    gc.collect()

    log.info(f" Dataset OK: {len(df)} filas, {len(df.columns)} columnas")
    log.info(f" Diccionario dinámico cargado: {len(event_dictionary)} eventos")

    return cfg, components_meta, all_columns, "ready", slider_range


# =====================================================
# CALLBACK — FIGURA INICIAL
# =====================================================
@app.callback(
    Output("initial-figure-store", "data"),
    [
        Input("current-columns", "data"),
        Input("cached-df", "data")
    ],
    prevent_initial_call=True
)
def preparar_figura_inicial(cols_all, df_ready):
    if df_ready != "ready" or not cols_all:
        return {}

    df = MAPA_DF.get("actual")
    components_meta = MAPA_DF.get("components_meta", {})
    event_dictionary = MAPA_DF.get("event_dictionary", {})

    if df is None:
        return {}

    opciones = build_checklist_options(cols_all)
    if not opciones:
        return {}

    col_visual = opciones[0]["value"]

    # Llamada ligera: pasar el diccionario actual
    fig = actualizar_grafico(
        columnas_seleccionadas=[col_visual],
        relayout_data=None,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=format_label_with_unit,
        columnas_info=components_meta,
        slider_data=None,
        event_dictionary=event_dictionary
    )

    # Liberar referencias locales y forzar GC
    try:
        out = fig.to_plotly_json()
    except Exception:
        out = {}
    del fig
    gc.collect()

    return out


# =====================================================
# CALLBACK PRINCIPAL DE GRÁFICO
# =====================================================
@app.callback(
    Output("grafico-temporal", "figure"),
    [
        Input("checklist-columnas", "value"),
        Input("initial-figure-store", "data"),
        Input("current-columns", "data"),
        Input("grafico-temporal", "relayoutData"),
        Input("slider-absolute-range", "data"),
    ]
)
def grafico_callback(columnas_sel, fig_inicial, columnas_info, relayout_data, slider_data):

    df = MAPA_DF.get("actual")
    components_meta = MAPA_DF.get("components_meta", {})
    event_dictionary = MAPA_DF.get("event_dictionary", {})

    if df is None:
        return {}

    # Si no hay selección, usamos la figura precargada (evitar cálculo pesado)
    if (not columnas_sel or len(columnas_sel) == 0) and fig_inicial:
        return fig_inicial

    fig = actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=relayout_data,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=format_label_with_unit,
        columnas_info=components_meta,
        slider_data=slider_data,
        event_dictionary=event_dictionary
    )

    return fig


# =====================================================
# FILTROS
# =====================================================
registrar_callbacks_filtros(app)


# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    log.info(f"🚀 Iniciando app en puerto {port}")
    app.run(debug=False, port=port)
