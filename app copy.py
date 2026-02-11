# =====================================================
# app.py — visor MLOps-aware con merge en RAM
# =====================================================

import dash
import logging
import os
import gc
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd
import plotly.graph_objects as go

from config_env import settings_env 

from utils.dataset.DatasetRegistry import DatasetRegistry
from generate_control_yml import generate_control_yml
from utils.cache_config import init_cache, cache_config, limpiar_cache
from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico
from utils.helpers import format_label_with_unit, build_checklist_options

from config_env import settings_env

# -----------------------------------------------------
# LOGGING
# -----------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# -----------------------------------------------------
# DATASETS REGISTRY
# -----------------------------------------------------
try:
    generate_control_yml()
except Exception as exc:
    log.error(f"❌ Error generando control.yml: {exc}")
    raise


# BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"
BASE_DATASETS_DIR = Path(settings_env.OUTPUT_CONTROL).parent
registry = DatasetRegistry(BASE_DATASETS_DIR)

datasets_disponibles = registry.list()
if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles")

DEFAULT_DATASET = registry.default_dataset
log.info(f"🧠 Dataset por defecto: {DEFAULT_DATASET}")

# -----------------------------------------------------
# PRECARGA DATASET POR DEFECTO
# -----------------------------------------------------
ds_default = registry.get_default()
df_default = ds_default.load_for_visualization()
x_timer_default = ds_default.main.timestamp_col

MAPA_DF_preload = {
    "df": df_default,
    "x_timer": x_timer_default,
}

log.info(
    f"🧠 Dataset inicial cargado → filas={len(df_default)} "
    f"eje_temporal='{x_timer_default}'"
)

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

# Almacén en RAM de la app
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
            x_timer=MAPA_DF_preload["x_timer"],
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

    # -------------------------------------------------
    # DEFAULT (ya precargado)
    # -------------------------------------------------
    if dataset_name == DEFAULT_DATASET:
        df = MAPA_DF_preload["df"]
        x_timer = MAPA_DF_preload["x_timer"]

        MAPA_DF.clear()
        MAPA_DF["actual"] = df
        MAPA_DF["x_timer"] = x_timer

        slider_range = {
            "min": df[x_timer].iloc[0],
            "max": df[x_timer].iloc[-1],
        }

        columnas = [
            {
                "name": col,
                "type": "tabular",
                "component": "main"
            }
            for col in df.columns
            if col != x_timer
        ]

        return {}, {}, columnas, "ready", slider_range


    # -------------------------------------------------
    # CARGA NORMAL
    # -------------------------------------------------
    try:
        limpiar_cache(cache)
    except Exception:
        pass

    MAPA_DF.clear()
    gc.collect()

    ds = registry.get(dataset_name)
    df = ds.load_for_visualization()
    x_timer = ds.main.timestamp_col

    # --------------------------------------------------
    # Construir metadata mínima desde el DataFrame
    # --------------------------------------------------
    components_meta = {}
    columns_meta = []

    for col in df.columns:
        if col == x_timer:
            continue

        # inferir componente por prefijo
        if "_" in col:
            comp = col.split("_")[0]
        else:
            comp = "main"

        components_meta.setdefault(comp, {
            "name": comp,
            "measurements": {}
        })

        components_meta[comp]["measurements"][col] = {
            "type": "tabular"
        }

        columns_meta.append({
            "name": col,
            "component": comp,
            "type": "tabular"
        })




    MAPA_DF["actual"] = df
    MAPA_DF["x_timer"] = x_timer

    slider_range = {
        "min": df[x_timer].iloc[0],
        "max": df[x_timer].iloc[-1],
    }

    return (
        {},
        components_meta,
        columns_meta,
        "ready",
        slider_range
    )


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
    if df_ready != "ready":
        return {}

    df = MAPA_DF.get("actual")
    x_timer = MAPA_DF.get("x_timer")

    if df is None or x_timer is None:
        return {}

    # Primera columna numérica como default (si existe)
    numeric_cols = [
        c for c in df.columns
        if c != x_timer and pd.api.types.is_numeric_dtype(df[c])
    ]

    if not numeric_cols:
        return {}

    col_visual = numeric_cols[0]

    fig = actualizar_grafico(
        columnas_seleccionadas=[col_visual],
        relayout_data=None,
        df_plot=df,
        x_timer=x_timer,
        format_label_with_unit=format_label_with_unit,
        columnas_info={},
        slider_data=None,
        event_dictionary={}
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
    x_timer = MAPA_DF.get("x_timer")

    if df is None or x_timer is None:
        return go.Figure()

    # -------------------------------------------------
    # MODO VACÍO
    # -------------------------------------------------
    if not columnas_sel:

        xmin = slider_data["min"]
        xmax = slider_data["max"]

        if relayout_data and "xaxis.range[0]" in relayout_data:
            xmin = relayout_data["xaxis.range[0]"]
            xmax = relayout_data["xaxis.range[1]"]

        fig = go.Figure()
        fig.update_layout(
            xaxis=dict(range=[xmin, xmax]),
            yaxis=dict(visible=False),
            showlegend=False,
            annotations=[
                dict(
                    text="No hay columnas seleccionadas",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    font=dict(size=22, color="gray"),
                )
            ],
        )
        return fig

    # -------------------------------------------------
    # NORMAL
    # -------------------------------------------------
    return actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=relayout_data,
        df_plot=df,
        x_timer=x_timer,
        format_label_with_unit=format_label_with_unit,
        columnas_info={},
        slider_data=slider_data,
        event_dictionary={}
    )

# =====================================================
# FILTROS
# =====================================================
registrar_callbacks_filtros(app)

# =====================================================
# MAIN
# =====================================================
if __name__ == "__main__":
    # port = int(os.environ.get("PORT", 8050))
    port = settings_env.SERVER_PORT
    app.run(debug=False, port=port)
