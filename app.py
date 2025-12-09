# =====================================================
# app.py — versión con precarga real y comportamiento corregido
# =====================================================

import dash
import logging
import os
from pathlib import Path
from dash.dependencies import Input, Output, State
from dash import html, dcc
import pandas as pd

from utils.dataset.DatasetRegistry import DatasetRegistry
from utils.cache_config import init_cache, cache_config
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

    ds = registry.get(dataset_name)
    cfg = ds.main.config if hasattr(ds, "main") else {}

    cols_info = ds.get_all_columns()
    components_meta = cols_info.get("components_meta", {})
    all_columns = cols_info.get("all", [])

    # Guardamos metadata global para actualizar_grafico()
    MAPA_DF["components_meta"] = components_meta

    save_debug_info(
        content_source=cols_info,
        filename=f"colls_info_{dataset_name}",
        head=f"HEADER DE cols_info para dataset '{dataset_name}': {ds.name}"
    )

    df = ds.df.copy()
    MAPA_DF["actual"] = df

    slider_range = {
        "min": df["Timestamp"].iloc[0],
        "max": df["Timestamp"].iloc[-1]
    }

    log.info(f" Dataset OK: {len(df)} filas, {len(df.columns)} columnas")

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
    if df is None:
        return {}

    # Opciones correctas del checklist
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
        slider_data=None
    )

    return fig.to_plotly_json()


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

    if df is None:
        return {}

    # Si no hay selección, usamos la figura precargada
    if (not columnas_sel or len(columnas_sel) == 0) and fig_inicial:
        return fig_inicial

    return actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=relayout_data,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=format_label_with_unit,
        columnas_info=components_meta,
        slider_data=slider_data
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
    log.info(f"🚀 Iniciando app en puerto {port}")
    app.run(debug=False, port=port)
