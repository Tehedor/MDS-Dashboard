# =====================================================
# app.py — versión corregida con modo vacío + mensaje UX
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
from utils.helpers import format_label_with_unit, build_checklist_options
import plotly.graph_objects as go

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

DEFAULT_DATASET = datasets_disponibles[0]
log.info(f"🧠 Precargando dataset inicial: {DEFAULT_DATASET}")

ds_default = registry.get(DEFAULT_DATASET)

cols_info_default = ds_default.get_all_columns()
df_default = ds_default._load_df_lazy()

# =====================================================
# FIX: Detectar dataset de eventos también en el default
# =====================================================
event_dictionary_default = {}
for sd in ds_default.secondary.values():
    if sd.type.lower() == "eventencodeddataset":
        event_dictionary_default = getattr(sd, "event_dictionary", {}) or {}
        break

MAPA_DF_preload = {
    "components_meta": cols_info_default.get("components_meta", {}),
    "all_columns": cols_info_default.get("all", []),
    "df": df_default,
    "event_dictionary": event_dictionary_default,
}

log.info(f"🧠 Dataset inicial precargado: {len(df_default)} filas, {len(df_default.columns)} columnas")
log.info(f"🧩 Diccionario de eventos precargado: {len(event_dictionary_default)} códigos")



log.info("##################################################")
log.info("##### http://localhost:8050/ #####################")
log.info("##################################################")

# -----------------------------------------------------
# DASH + CACHE
# -----------------------------------------------------
app = dash.Dash(__name__)
cache = init_cache(app)
cache_config(cache)
server = app.server

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
            default_dataset=DEFAULT_DATASET,
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

    # -----------------------------------------------------
    # ⚡ DEFAULT precargado
    # -----------------------------------------------------
    if dataset_name == DEFAULT_DATASET:
        df = MAPA_DF_preload["df"]
        components_meta = MAPA_DF_preload["components_meta"]
        all_columns = MAPA_DF_preload["all_columns"]
        event_dictionary = MAPA_DF_preload["event_dictionary"]

        MAPA_DF.clear()
        MAPA_DF["components_meta"] = components_meta
        MAPA_DF["event_dictionary"] = event_dictionary
        MAPA_DF["actual"] = df

        slider_range = {
            "min": pd.to_datetime(df["Timestamp"].iloc[0]),
            "max": pd.to_datetime(df["Timestamp"].iloc[-1]),
        }

        return {}, components_meta, all_columns, "ready", slider_range

    # -----------------------------------------------------
    # CARGA NORMAL
    # -----------------------------------------------------
    try:
        limpiar_cache(cache)
    except:
        pass

    MAPA_DF.clear()
    gc.collect()

    ds = registry.get(dataset_name)
    cfg = ds.main.config if hasattr(ds, "main") else {}

    cols_info = ds.get_all_columns()
    components_meta = cols_info.get("components_meta", {})
    all_columns = cols_info.get("all", [])

    MAPA_DF["components_meta"] = components_meta

    # event dictionary
    event_dictionary = {}
    for sd in ds.secondary.values():
        if sd.type.lower() == "eventencodeddataset":
            event_dictionary = getattr(sd, "event_dictionary", {}) or {}
            break

    MAPA_DF["event_dictionary"] = event_dictionary

    df = ds._load_df_lazy()
    MAPA_DF["actual"] = df

    if "Timestamp" not in df.columns:
        df["Timestamp"] = df.index

    slider_range = {
        "min": pd.to_datetime(df["Timestamp"].iloc[0]),
        "max": pd.to_datetime(df["Timestamp"].iloc[-1]),
    }

    return cfg, components_meta, all_columns, "ready", slider_range


# =====================================================
# FIGURA INICIAL
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

    opciones = build_checklist_options(cols_all)
    if not opciones:
        return {}

    col_visual = opciones[0]["value"]

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

    return fig.to_plotly_json()


# =====================================================
# GRAFICO PRINCIPAL (CON MODO VACÍO)
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
        return go.Figure()

    # -----------------------------------------------------
    # 🆕 MODO VACÍO — sin columnas seleccionadas
    # -----------------------------------------------------
    if not columnas_sel or len(columnas_sel) == 0:

        slider_min = pd.to_datetime(slider_data["min"])
        slider_max = pd.to_datetime(slider_data["max"])

        # ¿Había zoom?
        if relayout_data and "xaxis.range[0]" in relayout_data:
            xmin = pd.to_datetime(relayout_data["xaxis.range[0]"])
            xmax = pd.to_datetime(relayout_data["xaxis.range[1]"])
        elif relayout_data and "xaxis.range" in relayout_data:
            xmin, xmax = relayout_data["xaxis.range"]
            xmin, xmax = pd.to_datetime(xmin), pd.to_datetime(xmax)
        else:
            xmin, xmax = slider_min, slider_max

        fig = go.Figure()
        fig.update_layout(
            xaxis=dict(range=[xmin, xmax]),
            yaxis=dict(visible=False),
            showlegend=False,
            title="",
            annotations=[
                dict(
                    text="No hay columnas seleccionadas",
                    x=0.5, y=0.5,
                    xref="paper", yref="paper",
                    showarrow=False,
                    font=dict(size=22, color="gray")
                )
            ]
        )
        return fig

    # -----------------------------------------------------
    # NORMAL — columnas seleccionadas
    # -----------------------------------------------------
    return actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=relayout_data,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=format_label_with_unit,
        columnas_info=components_meta,
        slider_data=slider_data,
        event_dictionary=event_dictionary
    )


# =====================================================
# FILTROS
# =====================================================
registrar_callbacks_filtros(app)

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, port=port)
