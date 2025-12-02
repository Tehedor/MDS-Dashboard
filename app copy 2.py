# app.py
import dash
import logging
import os
from pathlib import Path
from dash.dependencies import Input, Output
from dash import html, dcc
import pandas as pd

from utils.dataset.DatasetRegistry import DatasetRegistry
from utils.cache_config import init_cache, cache_config

from layouts.dashboard_layout import serve_layout
from callbacks.filtros import registrar_callbacks_filtros
from callbacks.grafico_temporal import actualizar_grafico

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
log = logging.getLogger("App")

# ------------------------------------------------------------------------------
# 1) CARGA INICIAL – SOLO UNA VEZ
# ------------------------------------------------------------------------------
BASE_DATASETS_DIR = Path(__file__).parent / "Datasets"
registry = DatasetRegistry(BASE_DATASETS_DIR)

datasets_disponibles = registry.list()   # <-- ESTO ES UNA LISTA CORRECTA
if not datasets_disponibles:
    raise RuntimeError("❌ No hay datasets disponibles!")


# ------------------------------------------------------------------------------
# 2) DASH APP + CACHE
# ------------------------------------------------------------------------------
app = dash.Dash(__name__)
cache = init_cache(app)
cache_config(cache)
server = app.server

MAPA_DF = {}   # dataframe cache en memoria


# ------------------------------------------------------------------------------
# 3) LAYOUT – ZERO COST
# ------------------------------------------------------------------------------
def get_layout():
    return html.Div([
        dcc.Store(id="current-config"),
        dcc.Store(id="current-components"),
        dcc.Store(id="current-columns"),
        dcc.Store(id="cached-df"),

        serve_layout(
            config={},
            datasets=datasets_disponibles,      # 🔥 CORREGIDO
            opciones_checklist=[],
            columnas=[],
            x_timer="Timestamp",
            default_dataset=datasets_disponibles[0],   # ahora funciona
        ),
    ])

app.layout = get_layout


# ------------------------------------------------------------------------------
# 4) CALLBACK: CARGAR DATASET
# ------------------------------------------------------------------------------
@app.callback(
    [
        Output("current-config", "data"),
        Output("current-components", "data"),
        Output("current-columns", "data"),
        Output("cached-df", "data"),
    ],
    Input("dataset-selector", "value")
)
def cargar_dataset(dataset_name):

    log.info(f"➡ Cargando dataset {dataset_name} en caché...")

    ds = registry.get(dataset_name)
    cfg = ds.main.config if hasattr(ds, "main") else {}

    cols_info = ds.get_all_columns()
    components_meta = cols_info.get("components_meta", {})
    all_columns = cols_info.get("all", [])

    df = ds.df.copy()
    MAPA_DF["actual"] = df

    log.info(f" Dataset OK: {len(df)} filas, {len(df.columns)} columnas")

    return cfg, components_meta, all_columns, "ready"


# ------------------------------------------------------------------------------
# 5) CALLBACK GRÁFICO
# ------------------------------------------------------------------------------
@app.callback(
    Output("grafico-temporal", "figure"),
    [
        Input("checklist-columnas", "value"),
        Input("cached-df", "data"),
        Input("current-columns", "data"),
    ]
)
def grafico_callback(columnas_sel, trigger, columnas_info):
    df = MAPA_DF.get("actual")
    if df is None:
        return {}

    return actualizar_grafico(
        columnas_seleccionadas=columnas_sel,
        relayout_data=None,
        df_plot=df,
        x_timer="Timestamp",
        format_label_with_unit=lambda c: c,
        columnas_info=columnas_info,
    )


# ------------------------------------------------------------------------------
# CALLBACKS EXTRA
# ------------------------------------------------------------------------------
registrar_callbacks_filtros(app)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    log.info(f"🚀 Iniciando app en puerto {port}")
    app.run(debug=False, port=port)
